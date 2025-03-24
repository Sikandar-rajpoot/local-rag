from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.services.embedding import EmbeddingService
from src.services.retrieval import RetrievalService
from src.services.generation import GenerationService
from src.utils.logger import setup_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = setup_logger()
router = APIRouter(prefix="/rag", tags=["rag"])

class QueryRequest(BaseModel):
    query: str

# Dependency to provide services
def get_services():
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embedding_service = EmbeddingService(ollama_host)
    retrieval_service = RetrievalService(embedding_service)
    generation_service = GenerationService(ollama_host)
    return embedding_service, retrieval_service, generation_service

@router.post("/query")
async def query_rag(
    request: QueryRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService] = Depends(get_services)
):
    embedding_service, retrieval_service, generation_service = services
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Processing query: {query}")
    query_embedding = embedding_service.embed_query(query)
    retrieved_docs = retrieval_service.retrieve(query_embedding)
    if not retrieved_docs:
        raise HTTPException(status_code=404, detail="No relevant documents found")

    context = " ".join(retrieved_docs)
    response = generation_service.generate(query, context)
    logger.info(f"Generated response: {response}")
    return {"response": response}