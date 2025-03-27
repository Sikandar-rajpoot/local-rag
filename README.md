# Local RAG System

A `Retrieval-Augmented Generation (RAG)` system designed to run entirely offline using **FastAPI**, **ChromaDB**, and **Ollama**. This project leverages `nomic-embed-text` for embedding generation and `Mistral` or `Llama2` for text generation, making it perfect for secure, internet-independent environments after initial setup.

## 📌 Project Overview

The Local RAG System retrieves relevant document chunks from a local vector store (ChromaDB) based on user queries and generates concise, context-aware responses using a local language model (Ollama's `llama2` or `Mistral`). Built with a modular architecture, it’s easy to extend, customize, and deploy.

## 🚀 Features

- 🛠 **Fully Offline:** Operates without internet access using local models (`nomic-embed-text`, `llama2`) and a persistent ChromaDB vector store.
- ⚡ **FastAPI Backend:** Exposes a robust RESTful API for querying and managing the system.
- 🔗 **Modular Design:** Separates embedding, retrieval, and generation into distinct services for maintainability and scalability.
- 📚 **Custom Knowledge Base:** Supports loading custom `.txt` files into the `documents/` directory.
- 🔒 **Secure & Private:** Keeps all data and processing on your local machine.
- 📈 **Persistent History:** Maintains a permanent record of interactions in a `SQLite` database.

## 📂 Project Structure

```
rag-system/
│
├── documents/              # Directory for custom .txt files (knowledge base)
│   └── knowledge.txt       # Example document
├── src/                    # Source code
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application entry point
│   ├── routes/             # API endpoints
│   │   ├── __init__.py
│   │   └── rag.py          # RAG-specific routes
│   ├── services/           # Core logic
│   │   ├── __init__.py
│   │   ├── embedding.py    # Embedding generation
│   │   ├── generation.py   # Text generation
│   │   ├── retrieval.py    # Document retrieval and indexing
│   │   └── file_manager.py # File management utilities
│   └── utils/              # Helper functions
│       ├── __init__.py
│       └── logger.py       # Logging setup
├── ui/                     # Streamlit frontend
│   └── app.py              # UI application
├── chroma_db/              # ChromaDB storage (auto-generated)
├── db/                     # SQLite database for history (auto-generated)
│   └── history.db
├── cache/                  # Cached embeddings (auto-generated)
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## ⚙️ Prerequisites

Before setting up the **Local RAG System**, ensure you have the following installed:

- **🐍 Python 3.8+**: Ensure Python is installed on your system. [Download Python](https://www.python.org/downloads/)
- **🦙 Ollama**: A tool to run local language models. [Download from ollama.ai](https://ollama.ai/)
- **🛠 Git (Optional)**: For cloning the repository. [Download Git](https://git-scm.com/downloads)

## 📦 Installation

1. **Clone the repository:**

```
git clone <repository-url>
cd rag-system
```

(Or manually download and extract the project files.)

2. **Create and Activate a Virtual Environment:**

```
python -m venv venv
venv\Scripts\activate
```

3. **Install Dependencies:**

```
pip install -r requirements.txt
```

**Required packages:**

- fastapi==0.110.0
- uvicorn==0.29.0
- chromadb==0.4.24
- python-dotenv==1.0.1
- langchain==0.1.13
- ollama==0.1.7
- streamlit==1.32.0

4. Set Up Ollama

   1. Install Ollama:

   - Follow instructions at ollama.ai.

   2. Pull the required models:

   ```
   ollama pull llama2 # or mistral
   ollama pull nomic-embed-text
   ```

   3. Start the Ollama server:

   ```
   ollama serve
   ```

   Keep this running in a separate terminal.

5. Create a `.env` file in the root directory with the following variables:

```
OLLAMA_HOST=http://localhost:11434
ALLOWED_DIRS=D:/temp  # Optional: Restrict file operations to specific directories
```

Adjust the host if `Ollama runs` on a different port or machine.

6. Prepare the Knowledge Base:

- Add your .txt files to the documents/ directory.
- Example documents/knowledge.txt:

```
# Knowledge Base

The solar system consists of the Sun and eight planets. Earth is the third planet from the Sun.
```

7. Run the FastAPI server:

1. Run the FastAPI server:

   ```
   python -m src.main
   ```

   Server runs at `http://localhost:8000`. Documents are indexed into ChromaDB on startup if the collection is empty.

1. Start Streamlit UI:

   ```
   streamlit run ui/app.py
   ```

   Access the UI at `http://localhost:8501`.

- The server will start at `http://localhost:8000`.
- On startup, it loads documents into ChromaDB if the collection is empty.

## 🔍 API Documentation

The API is documented with Swagger UI at:

```
http://localhost:8000/docs
```

**Key Endpoints:**

- `POST /query`: Query the RAG system.
- `GET /history`: Get interaction history.
- `POST /file/upload`: Upload a file.

## 📝 Usage

1. **Query the RAG System:**

   ```
   curl -X POST "http://localhost:8000/rag/query" -H "Content-Type: application/json" -d '{"query": "What is the third planet?", "file_paths": ["documents/knowledge.txt"]}'
   ```

   Response: `{"response": "Earth is the third planet from the Sun.", ...}`

2. **Get Interaction History:**

   ```
   curl -X POST "http://localhost:8000/rag/automate" -H "Content-Type: application/json" -d '{"prompt": "Write an article to D:/temp/article.md about AI"}'
   ```

   Response: `[{"query": "What is the third planet?", ...}, ...]`

**Via Streamlit UI**

- **File RAG:** Enter a query (e.g., "What is the third planet?") and upload knowledge.txt.
- **File Automation:** Input "Delete all files from D:/temp" or "Search for \*.txt in D:/temp".
- **History:** View past interactions with timestamps.

## 🛠 Troubleshooting

- **Ollama Not Running:** Ensure `ollama` serve is active. Check `OLLAMA_HOST` in `.env`.
- **ChromaDB Errors:** Verify `chroma_db/` has write permissions. Delete it to re-index documents.
- **Model Not Found:** Run `ollama pull llama2` and `ollama pull nomic-embed-text` again.
- **API Fails:** Check logs in the terminal or `logs/` for detailed errors.

## 📝 Notes

- The system uses `nomic-embed-text` for embeddings and `llama2` for text generation.
- The `documents/` directory contains the knowledge base.
- The `db/` directory contains the SQLite database for history.
