import ollama
from src.utils.logger import setup_logger

logger = setup_logger()

class GenerationService:
    def __init__(self, ollama_host: str, model: str = "mistral"):
        self.client = ollama.Client(host=ollama_host)
        self.model = model

    def generate(self, query: str, context: str) -> str:
        # Updated prompt to request structured HTML output
        prompt = (
            f"Context: {context}\n\n"
            f"Query: {query}\n\n"
            "Generate a structured HTML response to the query based on the context. "
            "Use proper HTML tags like <h1> for the main heading, <p> for paragraphs, "
            "<ul> or <ol> for lists if applicable, and <strong> or <em> for emphasis. "
            "Ensure the response is concise, well-formatted, and visually organized. "
            "Return only the HTML content without any additional text or comments."
        )
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            html_response = response["response"].strip()
            # Wrap the response in a basic HTML structure for robustness
            full_html = (
                "<!DOCTYPE html>"
                "<html lang='en'>"
                "<head><meta charset='UTF-8'><style>"
                "body { font-family: 'Poppins', sans-serif; margin: 0; padding: 0; }"
                "h1 { font-size: 1.5rem; color: #a94f0a; margin-bottom: 10px; }"
                "p { margin: 5px 0; line-height: 1.5; }"
                "ul, ol { margin: 10px 0 10px 20px; color: #c07600; }"
                "strong { color: #9d660d; }"
                "em { color: #388e3c; }"
                "</style></head>"
                f"<body>{html_response}</body>"
                "</html>"
            )
            return full_html
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return (
                "<!DOCTYPE html>"
                "<html lang='en'><body>"
                "<h1>Error</h1>"
                "<p>An error occurred while generating the response.</p>"
                "</body></html>"
            )