from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from src.routes.rag import router as rag_router
from src.services.retrieval import RetrievalService
from src.services.embedding import EmbeddingService
from src.utils.logger import setup_logger

logger = setup_logger()
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up RAG system...")
    # Optional: Pre-load documents
    embedding_service = EmbeddingService(OLLAMA_HOST)
    retrieval_service = RetrievalService(embedding_service)
    retrieval_service.load_documents()
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="RAG System API",
    description="A Retrieval-Augmented Generation system using Ollama and Chroma.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(rag_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)