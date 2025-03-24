from ollama import Client as OllamaClient

class EmbeddingService:
    def __init__(self, host: str):
        self.client = OllamaClient(host=host)
        self.model = "nomic-embed-text"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            response = self.client.embeddings(model=self.model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embeddings(model=self.model, prompt=text)
        return response["embedding"]