# Local RAG System

This project implements a **Retrieval-Augmented Generation (RAG)** system that runs entirely **offline** using **FastAPI, ChromaDB, and Ollama**. It leverages `nomic-embed-text` for **embedding generation** and `llama2` for **text generation**, making it ideal for environments without internet access after the initial setup.

## 📌 Project Overview

The system retrieves **relevant document chunks** from a **local vector store** (ChromaDB) based on a user query and generates concise answers using a **local language model** (Ollama's `llama2`). It’s structured for **modularity, scalability, and ease of use**.

## 🚀 Features

- **🛠 Offline Operation:** Uses **local models** (`nomic-embed-text` and `llama2`) and a **persistent vector database** (ChromaDB).
- **⚡ FastAPI Backend:** Provides a **RESTful API** for querying the system.
- **🔗 Modular Design:** Embedding, retrieval, and generation logic are separated into distinct services.
- **📚 Customizable Knowledge Base:** Load your own `.txt` files into the `documents/` directory.

## 📂 Project Structure

```
rag-system/
│
├── documents/              # Folder for storing .txt files (knowledge base)
│   └── knowledge.txt       # Sample document
├── src/                    # Source code directory
│   ├── __init__.py         # Makes src a Python package
│   ├── main.py             # FastAPI app entry point
│   ├── routes/             # API routes
│   │   ├── __init__.py
│   │   └── rag.py          # RAG-related endpoints
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── embedding.py    # Embedding service
│   │   ├── generation.py   # Generation service
│   │   └── retrieval.py    # Retrieval and document loading service
│   └── utils/              # Utility functions
│       ├── __init__.py
│       └── logger.py       # Custom logger setup
├── chroma_db/              # Chroma database storage (auto-created)
├── .env                    # Environment variables
├── requirements.txt        # Project dependencies
└── README.md               # This file
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

4. Set Up Ollama

   1. Install Ollama:

   - Follow instructions at ollama.ai.

   2. Pull the required models:

   ```
   ollama pull llama2
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
```

Adjust the host if Ollama runs on a different port or machine.

6. Prepare the Knowledge Base:

- Add your .txt files to the documents/ directory.
- Example documents/knowledge.txt:

```
# Knowledge Base

The solar system consists of the Sun and eight planets. Earth is the third planet from the Sun.
```

7. Run the FastAPI server:

```
uvicorn src.main:app --reload
```

- The server will start at http://localhost:8000.
- On startup, it loads documents into ChromaDB if the collection is empty.

## 🔍 API Documentation

The API is documented with Swagger UI at:

```
http://localhost:8000/docs
```
