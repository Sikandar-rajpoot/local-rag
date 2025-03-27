import ollama
from src.utils.logger import setup_logger

logger = setup_logger()

class GenerationService:
    def __init__(self, ollama_host: str, model: str = "mistral"):
        self.client = ollama.Client(host=ollama_host)
        self.model = model

    def generate(self, query: str, context: str) -> str:
        prompt = f"Context: {context}\n\nQuery: {query}\n\nAnswer:"
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response["response"].strip()
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return "Error generating response"