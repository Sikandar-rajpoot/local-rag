import os
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from src.services.embedding import EmbeddingService
from src.utils.logger import setup_logger
from PyPDF2 import PdfReader
from docx import Document

logger = setup_logger()

class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, db_path: str = "./chroma_db", cache_dir: str = "./cache"):
        self.embedding_service = embedding_service
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="rag_collection", metadata={"hnsw:space": "cosine"}
        )
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.supported_types = {".txt", ".pdf", ".docx"}

    def load_documents(self):
        """Load all documents from the documents directory (optional pre-loading)."""
        documents_dir = "documents"
        if not os.path.exists(documents_dir):
            os.makedirs(documents_dir)
            logger.warning(f"Created empty documents directory at {documents_dir}")
            return

        for filename in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, filename)
            self.process_file(file_path)

    def process_file(self, file_path: str) -> list[str]:
        """Process a single file and load its chunks into Chroma with metadata."""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_types:
            logger.error(f"Unsupported file type: {file_path}")
            raise ValueError(f"Unsupported file type: {file_ext}. Supported types: {self.supported_types}")

        # Check cache
        cache_path = os.path.join(self.cache_dir, f"{os.path.basename(file_path)}.pkl")
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                chunks, embeddings, metadatas = pickle.load(f)
            logger.info(f"Loaded {len(chunks)} chunks from cache for {file_path}")
        else:
            # Extract text and split into chunks
            chunks, metadatas = self._extract_text(file_path)
            if not chunks:
                return []

            # Embed and cache
            embeddings = self.embedding_service.embed_documents(chunks)
            with open(cache_path, "wb") as f:
                pickle.dump((chunks, embeddings, metadatas), f)
            logger.info(f"Cached {len(chunks)} chunks for {file_path}")

        # Check if file is already indexed (avoid duplicates)
        existing_ids = self.collection.get()["ids"]
        chunk_ids = [f"{file_path}_chunk_{i}" for i in range(len(chunks))]
        new_ids = [cid for cid in chunk_ids if cid not in existing_ids]

        if new_ids:
            new_chunks = [chunks[i] for i in range(len(chunk_ids)) if chunk_ids[i] in new_ids]
            new_embeddings = [embeddings[i] for i in range(len(chunk_ids)) if chunk_ids[i] in new_ids]
            new_metadatas = [metadatas[i] for i in range(len(chunk_ids)) if chunk_ids[i] in new_ids]
            self.collection.add(ids=new_ids, embeddings=new_embeddings, documents=new_chunks, metadatas=new_metadatas)
            logger.info(f"Added {len(new_ids)} new chunks from {file_path} to Chroma")

        return chunks

    def _extract_text(self, file_path: str) -> tuple[list[str], list[dict]]:
        """Extract text from a file based on its type and split into chunks with metadata."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return [], []

        text = ""
        metadatas = []
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
            metadatas = [{"file": file_path, "source": "text"}] * (text.count("\n\n") + 1)
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
                    metadatas.append({"file": file_path, "source": f"page_{i+1}"})
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph.text:
                    text += paragraph.text + " "
                    metadatas.append({"file": file_path, "source": f"paragraph_{i+1}"})
        else:
            return [], []

        if not text.strip():
            logger.warning(f"No text extracted from {file_path}")
            return [], []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        if len(metadatas) > len(chunks):
            metadatas = metadatas[:len(chunks)]  # Truncate to match chunks
        elif len(metadatas) < len(chunks):
            metadatas.extend([metadatas[-1] if metadatas else {"file": file_path, "source": "unknown"}] * (len(chunks) - len(metadatas)))
        return chunks, metadatas

    def retrieve(self, query_embedding: list[float], n_results: int = 3) -> tuple[list[str], list[dict]]:
        """Retrieve relevant chunks and their metadata from Chroma, ensuring no None values."""
        results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas"])
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        
        # Ensure metadata is always a list of dicts, replacing None with a default
        default_meta = {"file": "unknown", "source": "unknown"}
        cleaned_metas = [meta if isinstance(meta, dict) else default_meta for meta in metas]
        
        # Pad or truncate metadata to match documents length
        if len(cleaned_metas) < len(docs):
            cleaned_metas.extend([default_meta] * (len(docs) - len(cleaned_metas)))
        elif len(cleaned_metas) > len(docs):
            cleaned_metas = cleaned_metas[:len(docs)]
        
        return docs, cleaned_metas