import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from src.services.embedding import EmbeddingService
from src.utils.logger import setup_logger

logger = setup_logger()

class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, db_path: str = "./chroma_db"):
        self.embedding_service = embedding_service
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="rag_collection", metadata={"hnsw:space": "cosine"}
        )

    def load_documents(self):
        documents_dir = "documents"
        if not os.path.exists(documents_dir):
            os.makedirs(documents_dir)
            logger.warning(f"Created empty documents directory at {documents_dir}")
            return

        all_chunks = []
        for filename in os.listdir(documents_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(documents_dir, filename), "r") as file:
                    text = file.read()
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""]
                )
                chunks = splitter.split_text(text)
                all_chunks.extend(chunks)

        if all_chunks:
            embeddings = self.embedding_service.embed_documents(all_chunks)
            chunk_ids = [f"chunk_{i}" for i in range(len(all_chunks))]
            self.collection.add(ids=chunk_ids, embeddings=embeddings, documents=all_chunks)
            logger.info(f"Loaded {len(all_chunks)} chunks into Chroma")
        else:
            logger.warning("No documents found to load")

    def retrieve(self, query_embedding: list[float], n_results: int = 3) -> list[str]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
        return results["documents"][0] if results["documents"] else []