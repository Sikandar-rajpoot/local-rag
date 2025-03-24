from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from src.routes.rag import router as rag_router
from src.services.retrieval import RetrievalService
from src.services.embedding import EmbeddingService
from src.utils.logger import setup_logger

logger = setup_logger()

# Load environment variables
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load documents into Chroma
    embedding_service = EmbeddingService(OLLAMA_HOST)
    retrieval_service = RetrievalService(embedding_service)
    if retrieval_service.collection.count() == 0:
        logger.info("Loading documents on startup...")
        retrieval_service.load_documents()
    yield  # Application runs here
    # Shutdown: Add cleanup if needed (optional)
    logger.info("Shutting down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG System API",
    description="A Retrieval-Augmented Generation system using Ollama and Chroma.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routes
app.include_router(rag_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)