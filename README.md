# Website Context Chatbot

A Chrome extension that lets users chat with any website using AI and retrieval-augmented generation (RAG). The extension reads the current webpage, sends the page context to a local FastAPI backend, retrieves relevant content, and generates grounded answers using OpenRouter or a local Ollama model.

## Features

- Chat with the current website directly from the browser
- Ask page-specific questions using retrieved website context
- Summarize and explain long or complex webpages
- Generate follow-up questions and helpful suggestions
- Compare two explicit sources with a dedicated Compare Tool
- Create structured visual outputs such as charts and flow diagrams
- Use OpenRouter models with Ollama as a local fallback
- Store and search page context with a local vector database

## Tech Stack

- JavaScript
- HTML
- CSS
- Python
- FastAPI
- Chrome Extension Manifest V3
- ChromaDB
- Sentence Transformers
- BGE Small EN v1.5
- BGE Reranker Base
- OpenRouter
- OpenRouter model: `nvidia/nemotron-3-super-120b-a12b:free`
- OpenRouter model: `openai/gpt-oss-120b:free`
- Ollama
- Ollama model: `qwen2.5:3b`
- BeautifulSoup
- DuckDuckGo Search
- PyPDF
- Uvicorn
- RAG

## Project Structure

```text
Website Chatbot/
|-- backend/
|   |-- handlers/           # Chat, retrieval, compare, document, and chart handlers
|   |   |-- compare_tool.py  # Dedicated Compare Tool pipeline
|   |   |-- compare_chat.py  # Compare extraction/classification helpers
|   |   `-- compare_cache.py # Cached structured extraction
|   |-- prompts/            # Prompt builders for chat and auxiliary tasks
|   |-- chroma_db/          # Local vector database data, ignored by git
|   |-- crawler.py
|   |-- llm.py
|   |-- llm_providers.py
|   |-- main.py             # FastAPI routes, including POST /compare
|   |-- rag.py
|   |-- scraper.py
|   |-- search.py
|   `-- requirements.txt
|-- frontend/
|   |-- background.js       # Chrome extension service worker
|   |-- content.js          # Widget logic, including Compare Tool UI
|   |-- manifest.json       # Extension manifest
|   `-- widget.css          # Widget and Compare Tool styles
|-- restart_backend.ps1
`-- test_comparison_pipeline.py
```

## Compare Tool Architecture

Compare is implemented as a separate tool, not as chat mode with mixed context.

```text
frontend/content.js
  Compare Tool UI
  runCompareTool()
  renderCompareResult()
        |
        v
backend/main.py
  POST /compare
        |
        v
backend/handlers/compare_tool.py
  exact Source A + exact Source B
  pass 1: extract structured facts independently
  pass 2: compare extracted facts deterministically
  final: ask the LLM only to explain the comparison result
```

The Compare Tool reuses `compare_chat.py` for document classification and structured extraction, and `compare_cache.py` for cached extraction results. It does not use chat history, conversation memory, external search, chat streaming, or mixed website/document retrieval.

## Setup

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd "Website Chatbot"
```

### 2. Create Backend Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `backend/.env` file:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OLLAMA_API_URL=http://localhost:11434
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
ENABLE_RERANKER=false
RERANKER_MODEL_NAME=BAAI/bge-reranker-base
OLLAMA_MODEL=qwen2.5:3b
```

Optional OpenRouter model override:

```env
OPENROUTER_MODELS=nvidia/nemotron-3-super-120b-a12b:free,openai/gpt-oss-120b:free
```

## Running the App

### Start the Backend

From the project root:

```powershell
.\restart_backend.ps1
```

Or manually:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

The backend runs locally on:

```text
http://localhost:8000
```

### Load the Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the `frontend` folder
5. Open any website and activate the extension

## Ollama Setup

Install Ollama and pull the local fallback model:

```powershell
ollama pull qwen2.5:3b
```

Make sure Ollama is running at:

```text
http://localhost:11434
```

## How It Works

1. The Chrome extension injects a chatbot widget into the active webpage.
2. Website and document chat use RAG-backed retrieval through the FastAPI backend.
3. Compare Tool sends exact Source A and Source B text to `POST /compare`.
4. The Compare Tool extracts structured facts independently from both sources.
5. It builds deterministic rows for matches, missing items, conflicts, extras, and score.
6. The LLM explains the already-built comparison instead of comparing mixed raw context.
7. The response is displayed inside the widget.

## Notes

- `backend/.env`, logs, cache folders, virtual environments, and local vector database files are ignored by git.
- Keep API keys out of commits.
- OpenRouter is used first when configured.
- Ollama is used as a local fallback when enabled.

## Hackathon Summary

Website Context Chatbot is a browser-based AI assistant that makes any website conversational. Instead of copying content into a separate chatbot, users can ask questions directly on the page and receive answers grounded in the website's actual content. Compare Tool adds a separate source-to-source comparison workflow for accurate side-by-side analysis.
