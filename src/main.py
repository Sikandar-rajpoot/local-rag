from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import sqlite3
from src.routes.rag import router as rag_router
from src.services.retrieval import RetrievalService
from src.services.embedding import EmbeddingService
from src.utils.logger import setup_logger

logger = setup_logger()
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DB_PATH = os.path.join("db", "history.db")

def init_db():
    """Initialize SQLite database for interaction history."""
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Drop existing table to update schema (for simplicity; in production, use migrations)
    cursor.execute("DROP TABLE IF EXISTS history")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'query' or 'automation'
            query TEXT NOT NULL,
            file_path TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Initialized SQLite database for history with type column")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up RAG system...")
    init_db()  # Initialize database
    embedding_service = EmbeddingService(OLLAMA_HOST)
    retrieval_service = RetrievalService(embedding_service)
    retrieval_service.load_documents()
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="RAG System API",
    description="A Retrieval-Augmented Generation system with file management and history.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(rag_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)