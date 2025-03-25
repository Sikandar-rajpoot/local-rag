from fastapi import APIRouter, HTTPException, Depends
from src.schema.rag import QueryRequest, QueryResponse, AutomationRequest, AutomationResponse
from src.services.embedding import EmbeddingService
from src.services.retrieval import RetrievalService
from src.services.generation import GenerationService
from src.services.file_manager import FileManager
from src.utils.logger import setup_logger
from dotenv import load_dotenv
import os
import json

load_dotenv()
logger = setup_logger()
router = APIRouter(prefix="/rag", tags=["rag"])

def get_services():
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embedding_service = EmbeddingService(ollama_host)
    retrieval_service = RetrievalService(embedding_service)
    generation_service = GenerationService(ollama_host)
    file_manager = FileManager()
    return embedding_service, retrieval_service, generation_service, file_manager

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService, FileManager] = Depends(get_services)
):
    embedding_service, retrieval_service, generation_service, _ = services
    query = request.query.strip()
    file_path = request.file_path.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Valid file path is required")

    logger.info(f"Processing query: {query} with file: {file_path}")
    retrieval_service.process_file(file_path)
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

@router.post("/automate", response_model=AutomationResponse)
async def automate_task(
    request: AutomationRequest,
    services: tuple[EmbeddingService, RetrievalService, GenerationService, FileManager] = Depends(get_services)
):
    _, _, generation_service, file_manager = services
    prompt = request.prompt.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    logger.info(f"Processing automation prompt: {prompt}")

    # LLM instruction parsing prompt
    instruction_prompt = (
        "You are a file management assistant. Parse the following user prompt and return ONLY a valid JSON string "
        "with 'task' and 'args'. Do not include any additional text, explanations, or comments. "
        "Supported tasks: create_file, read_file, update_file, delete_file, create_directory, move_file, search_files. "
        "Use 'file_path' for file operations, 'dir_path' for directories, 'src_path' and 'dest_dir' for moving files, "
        "and 'pattern' for searching. Examples:\n"
        "'Create a file /path/to/test.txt with content Hello' -> {\"task\": \"create_file\", \"args\": {\"file_path\": \"/path/to/test.txt\", \"content\": \"Hello\"}}\n"
        "'Read /path/to/test.txt' -> {\"task\": \"read_file\", \"args\": {\"file_path\": \"/path/to/test.txt\"}}\n"
        "'Move /path/to/test.txt to /path/to/archive' -> {\"task\": \"move_file\", \"args\": {\"src_path\": \"/path/to/test.txt\", \"dest_dir\": \"/path/to/archive\"}}\n"
        "'Search for *.txt in /path/to/dir' -> {\"task\": \"search_files\", \"args\": {\"dir_path\": \"/path/to/dir\", \"pattern\": \"*.txt\"}}\n"
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

    result = file_manager.execute_task(task, args)
    logger.info(f"Automation result: {result}")
    return {"result": result}