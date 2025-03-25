from fastapi import APIRouter, HTTPException, Depends
from src.schema.rag import QueryRequest, QueryResponse
from src.services.embedding import EmbeddingService
from src.services.retrieval import RetrievalService
from src.services.generation import GenerationService
from src.utils.logger import setup_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = setup_logger()
router = APIRouter(prefix="/rag", tags=["rag"])

def get_services():
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embedding_service = EmbeddingService(ollama_host)
    retrieval_service = RetrievalService(embedding_service)
    generation_service = GenerationService(ollama_host)
    return embedding_service, retrieval_service, generation_service

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService] = Depends(get_services)
):
    embedding_service, retrieval_service, generation_service = services
    query = request.query.strip()
    file_path = request.file_path.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Valid file path is required")

    logger.info(f"Processing query: {query} with file: {file_path}")

    # Process the file
    retrieval_service.process_file(file_path)

    # Embed the query and retrieve relevant chunks with metadata
    query_embedding = embedding_service.embed_query(query)
    retrieved_docs, retrieved_metas = retrieval_service.retrieve(query_embedding)
    if not retrieved_docs:
        raise HTTPException(status_code=404, detail="No relevant documents found for the query")

    context = " ".join(retrieved_docs)
    response = generation_service.generate(query, context)
    logger.info(f"Generated response: {response}")
    return {
        "response": response,
        "context": retrieved_docs,
        "metadata": retrieved_metas
    }