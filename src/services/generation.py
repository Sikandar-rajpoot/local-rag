from ollama import Client as OllamaClient
from src.utils.logger import setup_logger

logger = setup_logger()

class GenerationService:
    def __init__(self, host: str):
        self.client = OllamaClient(host=host)
        self.model = "mistral" # Using Mistral model instead of Llama2

    def generate(self, query: str, context: str) -> str:
        prompt = (
            "You are a helpful assistant. Use the following context to answer the question concisely and accurately.\n"
            f"Context: {context}\n"
            f"Question: {query}\n"
            "Answer in 1-2 sentences:"
        )
        response = self.client.generate(model=self.model, prompt=prompt)
        return response["response"]