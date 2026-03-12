# PlanWise AI | Setup & Execution Guide

Follow these steps to successfully clone, configure, and run **PlanWise AI** on your local machine or a new system.

## 1. Prerequisites

Before starting, ensure your system has the following installed:
- **Python 3.9+**: The core runtime for the application.
- **Ollama**: Required to run the local LLMs. 
- **Ollama Connection**: Ensure Ollama is running at `http://localhost:11434`.

## 2. Setting Up the AI Engine (Ollama)

PlanWise AI relies on local models for high-performance strategic synthesis and chat reasoning. Open your terminal and run the following commands to pull the necessary models:

```bash
# Model for Strategic Synthesis (Baseline)
ollama pull qwen2.5:3b

# Model for Chat Reasoning & Planning
ollama pull deepseek-r1:8b

# Model for Neural Vector Embeddings (RAG context)
ollama pull nomic-embed-text:latest
```

## 3. Local Project Setup

### Clone the Repository
Open your terminal and navigate to your target directory:
```bash
git clone <repository-url>
cd "Planwise AI"
```

### Install Dependencies
It is recommended to use a virtual environment:
```bash
# Create a virtual environment
python -m venv venv

# Activate it (on macOS/Linux):
source venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt
```

## 4. Environment Configuration

Create a `.env` file in the root directory to define your local configurations:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

## 5. Running the Application

Ensure Ollama is running in the background, then execute the following command from the project root:

```bash
python app.py
```

The server will initialize on: `http://localhost:8000`

---

## 🛠️ Internal Architecture Overview

- **`app.py`**: The FastAPI backend managing the synthesis engine, RAG pipeline, and API endpoints.
- **`chroma_db/`**: Automatically generated directory for persistent vector storage.
- **`static/`**: Source for frontend assets and styles.
- **`templates/`**: HTML templates for the PlanWise UI.
