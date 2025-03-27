from fastapi import APIRouter, HTTPException, Depends
from src.schema.rag import QueryRequest, AutomationRequest, QueryResponse, AutomationResponse, HistoryEntry
from src.services.embedding import EmbeddingService
from src.services.retrieval import RetrievalService
from src.services.generation import GenerationService
from src.services.file_manager import FileManager
from src.utils.logger import setup_logger
from dotenv import load_dotenv
import os
import json
import sqlite3
from typing import List

load_dotenv()
logger = setup_logger()
router = APIRouter(prefix="/rag", tags=["rag"])
DB_PATH = os.path.join("db", "history.db")

def get_services():
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embedding_service = EmbeddingService(ollama_host)
    retrieval_service = RetrievalService(embedding_service)
    generation_service = GenerationService(ollama_host, model="mistral")
    file_manager = FileManager()
    return embedding_service, retrieval_service, generation_service, file_manager

def store_interaction(interaction_type: str, query: str, file_paths: List[str], response: str, details: str = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (type, query, file_paths, response, details) VALUES (?, ?, ?, ?, ?)",
            (interaction_type, query, json.dumps(file_paths), response, details)
        )
        conn.commit()
        conn.close()
        logger.info(f"Stored {interaction_type} interaction: {query}")
    except Exception as e:
        logger.error(f"Failed to store {interaction_type} interaction: {str(e)}")

def store_file_content(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO files (file_path, content) VALUES (?, ?)",
            (file_path, content)
        )
        conn.commit()
        conn.close()
        logger.info(f"Stored content for file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to store file content {file_path}: {str(e)}")

def get_db_content() -> List[str]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM files")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch DB content: {str(e)}")
        return []

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService, FileManager] = Depends(get_services)
):
    embedding_service, retrieval_service, generation_service, _ = services
    query = request.query.strip()
    file_paths = [fp.strip() for fp in request.file_paths if fp.strip()]

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Processing query: {query} with files: {file_paths}")

    # Get previous query for context
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT query FROM history WHERE type = 'query' ORDER BY timestamp DESC LIMIT 1")
    prev_query = cursor.fetchone()
    prev_query = prev_query[0] if prev_query else ""
    conn.close()

    retrieved_docs, retrieved_metas = [], []
    if file_paths:
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail=f"File not found: {file_path}")
            store_file_content(file_path)
            retrieval_service.process_file(file_path)
        query_embedding = embedding_service.embed_query(query)
        retrieved_docs, retrieved_metas = retrieval_service.retrieve(query_embedding)
    else:
        query_embedding = embedding_service.embed_query(query)
        retrieved_docs, retrieved_metas = retrieval_service.retrieve(query_embedding)
        if not retrieved_docs:
            db_content = get_db_content()
            if not db_content:
                raise HTTPException(status_code=404, detail="No data available in database")
            embeddings = embedding_service.embed_documents(db_content)
            scores = [sum(a * b for a, b in zip(query_embedding, emb)) / (sum(a * a for a in query_embedding) ** 0.5 * sum(b * b for b in emb) ** 0.5) for emb in embeddings]
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
            retrieved_docs = [db_content[i] for i in top_indices]
            retrieved_metas = [{"file": "Database", "source": "stored_content"}] * len(retrieved_docs)

    if not retrieved_docs:
        raise HTTPException(status_code=404, detail="No relevant documents found")

    context = " ".join(retrieved_docs)
    full_prompt = f"Previous query: {prev_query}\nCurrent query: {query}"
    response = generation_service.generate(full_prompt, context)
    logger.info(f"Generated response: {response}")

    store_interaction("query", query, file_paths, response)
    return {"response": response, "context": retrieved_docs, "metadata": retrieved_metas}

@router.post("/automate", response_model=AutomationResponse)
async def automate_task(
    request: AutomationRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService, FileManager] = Depends(get_services)
):
    embedding_service, retrieval_service, generation_service, file_manager = services
    prompt = request.prompt.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    logger.info(f"Processing automation prompt: {prompt}")
    instruction_prompt = (
        "You are a file management assistant. Parse the following user prompt and return a JSON object with 'task' and 'args'. "
        "Supported tasks: create_file, read_file, update_file, delete_file, create_directory, move_file, search_files, write_article, delete_all_files. "
        "Args can include 'file_paths' (list), 'file_path', 'dir_path', or 'pattern'. For 'write_article', use 'file_path' (supports .md or .html), 'source' (e.g., 'vector_db'), and 'content'. "
        "Examples:\n"
        "'Create files /path/test1.txt and /path/test2.txt with content Hello' -> {'task': 'create_file', 'args': {'file_paths': ['/path/test1.txt', '/path/test2.txt'], 'content': 'Hello'}}\n"
        "'Write an article to /path/article.md from vector database' -> {'task': 'write_article', 'args': {'file_path': '/path/article.md', 'source': 'vector_db'}}\n"
        "'Search for *.txt in /path/dir' -> {'task': 'search_files', 'args': {'dir_path': '/path/dir', 'pattern': '*.txt'}}\n"
        "'Delete all files from /path/dir' -> {'task': 'delete_all_files', 'args': {'dir_path': '/path/dir'}}\n"
        f"User prompt: {prompt}"
    )
    response = generation_service.client.generate(model="mistral", prompt=instruction_prompt)
    try:
        instruction = json.loads(response["response"])
        task = instruction.get("task")
        args = instruction.get("args", {})
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse LLM response: {str(e)} - Response: {response['response']}")
        raise HTTPException(status_code=500, detail="Failed to interpret prompt")

    file_paths = args.get("file_paths", [args.get("file_path", "")])
    if task == "write_article":
        file_path = file_paths[0]
        if "source" in args and args["source"] == "vector_db":
            query_embedding = embedding_service.embed_query("Generate an article based on available data")
            docs, _ = retrieval_service.retrieve(query_embedding, n_results=5)
            content = generation_service.generate("Write an article using this data", " ".join(docs))
        else:
            content_prompt = args.get("content", "")
            content = generation_service.generate(f"Write an article {content_prompt}", "")
        
        # Format content based on file extension
        if file_path.endswith(".md"):
            content = f"# Article\n\n{content.replace('\n', '\n\n')}"
        elif file_path.endswith(".html"):
            content = f"<!DOCTYPE html>\n<html>\n<head><title>Article</title></head>\n<body>\n<h1>Article</h1>\n<p>{content.replace('\n', '</p>\n<p>')}</p>\n</body>\n</html>"
        
        result = file_manager.execute_task("create_file", {"file_path": file_path, "content": content})
    elif task == "delete_all_files":
        dir_path = args.get("dir_path", "")
        if not dir_path or not os.path.isdir(dir_path):
            raise HTTPException(status_code=400, detail=f"Invalid directory: {dir_path}")
        results = []
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                results.append(file_manager.execute_task("delete_file", {"file_path": file_path}))
        result = "; ".join(results) if results else "No files to delete"
    elif task in ["create_file", "read_file", "update_file", "delete_file"]:
        results = [file_manager.execute_task(task, {"file_path": fp, "content": args.get("content", "")}) for fp in file_paths if fp]
        result = "; ".join(results)
    elif task == "search_files":
        result = file_manager.execute_task(task, {"dir_path": args.get("dir_path", ""), "pattern": args.get("pattern", "*")})
    else:
        result = file_manager.execute_task(task, args)

    logger.info(f"Automation result: {result}")
    details = json.dumps({"task": task, "args": args})
    store_interaction("automation", prompt, file_paths if task != "delete_all_files" else [args.get("dir_path", "")], result, details)
    return {"result": result}

@router.get("/history", response_model=List[HistoryEntry])
async def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, query, file_paths, response, details, timestamp FROM history ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        history = [
            {
                "id": row[0], "type": row[1], "query": row[2], "file_paths": row[3],
                "response": row[4], "details": row[5], "timestamp": row[6]
            }
            for row in rows
        ]
        logger.info(f"Fetched {len(history)} history entries")
        return history
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")