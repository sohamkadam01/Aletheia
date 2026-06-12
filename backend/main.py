from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import base64
import hashlib
import io
import json
import os
import sys
import time
import threading
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
import uvicorn

# Relative imports from the same directory
from handlers import chat_context, chat_response, chat_retrieval, chat_utils, chart_tool, compare_tool, document_chat, website_chat
from crawler import crawl_website, site_key
from scraper import clean_html_content, clean_text, decode_bytes
from rag import (
    NORMAL_CONTEXT_MAX_CHARS,
    content_hash,
    delete_old_collections,
    get_collection_stats,
    get_page_cache_status,
    is_content_current,
    is_link_question,
    process_and_store_document,
    process_and_store_pages,
    process_and_store_content,
    retrieve_context_with_sources,
)
from llm import (
    OLLAMA_MODEL,
    analyze_website_safety,
    generate_answer,
    generate_starter_questions,
    list_openrouter_models,
    list_ollama_models,
    needs_external_search,
    rewrite_follow_up_question,
    stream_answer,
)
from prompts.chat import is_flowchart_request
from search import search_duckduckgo

app = FastAPI(title="Website Chatbot API")
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "12"))
ANSWER_CACHE_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", "900"))
ANSWER_CACHE_MAX_ITEMS = int(os.getenv("ANSWER_CACHE_MAX_ITEMS", "200"))
rate_limit_bucket: dict[str, list[float]] = {}
answer_cache: dict[str, tuple[float, dict]] = {}
feedback_store: dict[str, list[dict]] = defaultdict(list)
cancel_events: dict[str, threading.Event] = {}
indexing_lock = threading.Lock()
active_indexing_jobs: set[str] = set()
OBSERVABILITY_MAX_EVENTS = int(os.getenv("OBSERVABILITY_MAX_EVENTS", "500"))
observability_events: list[dict] = []

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(chrome-extension://.*|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IndexRequest(BaseModel):
    url: str
    content: str

class ChatRequest(BaseModel):
    url: str
    question: str
    request_id: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    history: Optional[list[dict]] = None
    ollama_model: Optional[str] = None
    openrouter_model: Optional[str] = None
    force_provider: Optional[str] = None
    allow_external_search: bool = False
    concise_answer: bool = False
    document_id: Optional[str] = None
    document_mode: str = "website"
    fetched_webpage_text: Optional[str] = None
    fetched_webpage_url: Optional[str] = None
    conversation_memory: Optional[dict] = None

class CacheStatusRequest(BaseModel):
    url: str
    content_hash: Optional[str] = None

class CleanupRequest(BaseModel):
    max_age_days: int = 14

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 10

class FeedbackRequest(BaseModel):
    url: str
    question: str
    answer: str
    rating: str
    provider: Optional[str] = None
    model: Optional[str] = None
    sources: Optional[list[dict]] = None

class StarterRequest(BaseModel):
    url: str
    content_hash: Optional[str] = None
    title: Optional[str] = None

class PageSummaryRequest(BaseModel):
    url: str
    title: Optional[str] = None
    content: str
    summary_type: str = "quick"
    ollama_model: Optional[str] = None
    openrouter_model: Optional[str] = None
    force_provider: Optional[str] = None

class CancelRequest(BaseModel):
    request_id: str

class DocumentUploadRequest(BaseModel):
    filename: str
    content_base64: str
    mime_type: Optional[str] = None
    page_url: Optional[str] = None

class ChartRequest(BaseModel):
    url: str
    question: str
    content: Optional[str] = None
    content_hash: Optional[str] = None
    title: Optional[str] = None
    ollama_model: Optional[str] = None
    openrouter_model: Optional[str] = None
    force_provider: Optional[str] = None
    document_id: Optional[str] = None
    document_mode: str = "website"
    fetched_webpage_text: Optional[str] = None
    fetched_webpage_url: Optional[str] = None
    history: Optional[list[dict]] = None
    conversation_memory: Optional[dict] = None

class FlowchartRequest(BaseModel):
    url: str
    question: str
    content: Optional[str] = None
    content_hash: Optional[str] = None
    title: Optional[str] = None
    ollama_model: Optional[str] = None
    openrouter_model: Optional[str] = None
    force_provider: Optional[str] = None
    document_id: Optional[str] = None
    document_mode: str = "website"
    fetched_webpage_text: Optional[str] = None
    fetched_webpage_url: Optional[str] = None
    history: Optional[list[dict]] = None
    conversation_memory: Optional[dict] = None

class CompareRequest(BaseModel):
    document_a_text: str
    document_a_label: Optional[str] = "Document A"
    document_b_text: str
    document_b_label: Optional[str] = "Document B"
    compare_goal: Optional[str] = "Compare the two sources"
    ollama_model: Optional[str] = None
    openrouter_model: Optional[str] = None
    force_provider: Optional[str] = None

    class Config:
        extra = "forbid"

def normalize_page_content(content: str) -> str:
    if "<" in content and ">" in content:
        return clean_html_content(content)
    lines = [" ".join(line.split()) for line in content.splitlines()]
    return "\n".join(line for line in lines if line)

def document_collection_url(document_id: str) -> str:
    return f"document://{document_id}"

def safe_document_filename(filename: str) -> str:
    cleaned = os.path.basename(filename or "uploaded-document").strip()
    return cleaned[:120] or "uploaded-document"

def extract_docx_text(data: bytes) -> str:
    paragraphs = []
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        document_names = [
            name for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml") and ("document.xml" in name or "header" in name or "footer" in name)
        ]
        for name in document_names:
            root = ET.fromstring(archive.read(name))
            for paragraph in root.findall(".//w:p", namespaces):
                text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespaces)).strip()
                text = clean_text(text)
                if text:
                    paragraphs.append(text)
    return "\n".join(paragraphs)

def extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        venv_site_packages = os.path.join(os.path.dirname(__file__), "venv", "Lib", "site-packages")
        if os.path.isdir(venv_site_packages) and venv_site_packages not in sys.path:
            sys.path.insert(0, venv_site_packages)
            try:
                from pypdf import PdfReader
            except Exception as retry_exc:
                raise HTTPException(status_code=500, detail="PDF support requires pypdf. Restart with restart_backend.bat.") from retry_exc
        else:
            raise HTTPException(status_code=500, detail="PDF support requires pypdf. Restart with restart_backend.bat.") from exc
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = clean_text(text)
        if text.strip():
            pages.append(f"Page {index + 1}\n{text.strip()}")
    return "\n\n".join(pages)

def extract_document_text(filename: str, data: bytes) -> str:
    extension = os.path.splitext(filename.lower())[1]
    if extension == ".pdf":
        return extract_pdf_text(data)
    if extension == ".docx":
        return extract_docx_text(data)
    if extension in (".txt", ".md", ".csv", ".json", ".html", ".htm"):
        return clean_text(decode_bytes(data))
    raise HTTPException(status_code=400, detail="Unsupported document type. Upload PDF, DOCX, TXT, MD, CSV, JSON, or HTML.")

def answer_cache_key(url, text_hash, question, ollama_model="", openrouter_model="", force_provider="", concise_answer=False):
    return (
        f"{url}|{text_hash}|{chat_utils.normalize_question(question)}"
        f"|provider:{force_provider or 'auto'}"
        f"|openrouter:{openrouter_model or 'default'}"
        f"|ollama:{ollama_model or OLLAMA_MODEL}"
        f"|concise:{int(concise_answer)}"
    )

def get_cached_answer(key: str):
    cached = answer_cache.get(key)
    if not cached:
        return None
    cached_at, answer = cached
    if time.time() - cached_at > ANSWER_CACHE_TTL_SECONDS:
        answer_cache.pop(key, None)
        return None
    return answer

def store_cached_answer(key: str, response: dict) -> None:
    if len(answer_cache) >= ANSWER_CACHE_MAX_ITEMS:
        oldest_key = min(answer_cache, key=lambda k: answer_cache[k][0])
        answer_cache.pop(oldest_key, None)
    answer_cache[key] = (time.time(), response)

def feedback_key(url: str) -> str:
    return url.rstrip("/") or url

def feedback_guidance_for_url(url: str) -> str:
    items = feedback_store.get(feedback_key(url), [])[-8:]
    if not items:
        return ""
    helpful = [i for i in items if i.get("rating") == "up"]
    unhelpful = [i for i in items if i.get("rating") == "down"]
    guidance = []
    if helpful:
        guidance.append("Prefer answer styles that users marked helpful: concise, source-grounded, and well formatted.")
    if unhelpful:
        bad_questions = "; ".join(i.get("question", "")[:80] for i in unhelpful[-3:] if i.get("question"))
        guidance.append(f"Be extra careful on similar questions previously marked unhelpful: {bad_questions}")
    return "\n".join(guidance)

def observe_event(event_type: str, payload: dict) -> None:
    event = {"type": event_type, "timestamp": int(time.time()), **payload}
    observability_events.append(event)
    del observability_events[:-OBSERVABILITY_MAX_EVENTS]
    print("Observability:", json.dumps(event, ensure_ascii=False, default=str))

def rate_limit_chat(key: str) -> bool:
    now = time.time()
    recent = [t for t in rate_limit_bucket.get(key, []) if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
        rate_limit_bucket[key] = recent
        return False
    recent.append(now)
    rate_limit_bucket[key] = recent
    return True

def cancellation_event(request_id):
    if not request_id:
        return threading.Event()
    event = cancel_events.get(request_id)
    if event is None:
        event = threading.Event()
        cancel_events[request_id] = event
    return event

def raise_if_cancelled(cancel_event):
    if cancel_event.is_set():
        raise HTTPException(status_code=499, detail="Request cancelled.")

def is_local_vector_store_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "hnsw segment reader" in message
        or "nothing found on disk" in message
        or "error executing plan" in message
        or ("collection" in message and "does not exist" in message)
    )

def safe_is_content_current(url: str, text_hash: str) -> bool:
    try:
        return is_content_current(url, text_hash)
    except Exception as exc:
        if is_local_vector_store_error(exc):
            print(f"Local vector cache unavailable while checking content freshness: {exc}")
            return False
        raise

def safe_process_and_store_content(url: str, text: str) -> dict:
    try:
        return process_and_store_content(url, text)
    except Exception as exc:
        if is_local_vector_store_error(exc):
            print(f"Local vector cache unavailable while indexing page: {exc}")
            return {"indexed": False, "reason": "local_vector_cache_unavailable"}
        raise

def schedule_page_index(url: str, text: str, text_hash: str = "") -> None:
    if not url or not text or len(text.strip()) < 20:
        return
    job_key = f"{url}|{text_hash or content_hash(text)}"
    with indexing_lock:
        if job_key in active_indexing_jobs:
            return
        active_indexing_jobs.add(job_key)

    def run_index():
        try:
            if not safe_is_content_current(url, text_hash or content_hash(text)):
                safe_process_and_store_content(url, text)
        except Exception as exc:
            print(f"Background page indexing failed: {exc}")
        finally:
            with indexing_lock:
                active_indexing_jobs.discard(job_key)

    threading.Thread(target=run_index, daemon=True).start()

def safe_retrieve_context_with_sources(
    url: str,
    question: str,
    n_results: int = 5,
    context_max_chars: int = NORMAL_CONTEXT_MAX_CHARS,
) -> dict:
    try:
        return retrieve_context_with_sources(
            url,
            question,
            n_results=n_results,
            context_max_chars=context_max_chars,
        )
    except Exception as exc:
        if is_local_vector_store_error(exc):
            print(f"Local vector cache unavailable while retrieving context: {exc}")
            retrieval = chat_utils.empty_retrieval("Local vector cache unavailable.")
            retrieval["retrieval_mode"] = "local_vector_cache_unavailable"
            return retrieval
        raise

def stream_json_event(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"

def _autodetect_provider(request) -> None:
    """Set force_provider from model selection if not already set."""
    if not request.force_provider:
        if request.ollama_model:
            request.force_provider = "ollama"
        elif request.openrouter_model:
            request.force_provider = "openrouter"


@app.get("/")
async def root():
    return {"status": "online", "message": "Website Chatbot API is running"}

@app.get("/ollama-models")
async def ollama_models():
    models = list_ollama_models()
    selected = OLLAMA_MODEL if OLLAMA_MODEL in models else (models[0] if models else OLLAMA_MODEL)
    openrouter_models = list_openrouter_models()
    return {
        "models": models,
        "default_model": OLLAMA_MODEL,
        "selected_model": selected,
        "ollama_models": models,
        "default_ollama_model": OLLAMA_MODEL,
        "selected_ollama_model": selected,
        "openrouter_models": openrouter_models,
        "default_openrouter_model": openrouter_models[0] if openrouter_models else "",
        "default_provider": "openrouter"
    }

@app.get("/observability")
async def observability(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"events": observability_events[-safe_limit:], "count": len(observability_events), "max_events": OBSERVABILITY_MAX_EVENTS}

@app.post("/index")
async def index_website(request: IndexRequest):
    try:
        if not request.content or len(request.content.strip()) < 10:
            return {"indexed": False, "reason": "insufficient_content", "content_hash": ""}
        cleaned_text = normalize_page_content(request.content)
        result = process_and_store_content(request.url, cleaned_text)
        return result
    except Exception as e:
        print(f"Error in /index: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to index page content.")

@app.post("/cache-status")
async def cache_status(request: CacheStatusRequest):
    try:
        return get_page_cache_status(request.url, request.content_hash or "")
    except Exception as e:
        print(f"Error in /cache-status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read cache status.")

@app.get("/stats")
async def collection_stats(url: str):
    try:
        return get_collection_stats(url)
    except Exception as e:
        print(f"Error in /stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read collection stats.")

@app.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    try:
        rating = request.rating.lower().strip()
        if rating not in ("up", "down"):
            raise HTTPException(status_code=400, detail="Feedback rating must be 'up' or 'down'.")
        item = {
            "url": request.url, "question": request.question[:500], "answer": request.answer[:1200],
            "rating": rating, "provider": request.provider, "model": request.model,
            "sources": request.sources or [], "created_at": int(time.time()),
        }
        key = feedback_key(request.url)
        feedback_store[key].append(item)
        feedback_store[key] = feedback_store[key][-100:]
        observe_event("feedback", {"url": request.url, "question": request.question[:220], "rating": request.rating,
            "provider": request.provider or "", "model": request.model or "", "source_count": len(request.sources or [])})
        return {"stored": True, "count": len(feedback_store[key])}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record feedback.")

@app.post("/starter-questions")
async def starter_questions(request: StarterRequest):
    try:
        retrieval = retrieve_context_with_sources(request.url, "main topics, user goals, important links, pricing, contact")
        context = retrieval.get("context", "")
        if not context:
            return {"suggestions": ["Summarize this page", "What are the key takeaways?", "Explain simply"]}
        questions = generate_starter_questions(context, request.title or "")
        return {"suggestions": questions[:3] or ["Summarize this page", "What are the key takeaways?", "Explain simply"]}
    except Exception as e:
        print(f"Error in /starter-questions: {str(e)}")
        return {"suggestions": ["Summarize this page", "What are the key takeaways?", "Explain simply"]}

@app.post("/compare")
def compare_sources(request: CompareRequest):
    try:
        _autodetect_provider(request)
        return compare_tool.run_compare_tool(
            document_a=request.document_a_text,
            document_b=request.document_b_text,
            compare_goal=request.compare_goal or "Compare the two sources",
            labels={
                "a": request.document_a_label or "Document A",
                "b": request.document_b_label or "Document B",
            },
            model_options={
                "ollama_model": request.ollama_model,
                "openrouter_model": request.openrouter_model,
                "force_provider": request.force_provider or "",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /compare: {str(e)}")
        raise HTTPException(status_code=500, detail="Compare Tool failed to compare the two sources.")


@app.post("/compare/stream")
def stream_compare_sources(request: CompareRequest):
    def events():
        started_at = time.perf_counter()
        try:
            _autodetect_provider(request)
            payload = compare_tool.build_compare_tool_payload(
                document_a=request.document_a_text,
                document_b=request.document_b_text,
                compare_goal=request.compare_goal or "Compare the two sources",
                labels={
                    "a": request.document_a_label or "Document A",
                    "b": request.document_b_label or "Document B",
                },
            )
            result = payload["result"]
            yield stream_json_event({
                "type": "compare_result",
                "result": result,
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", "compare tool"),
            })

            full_answer = ""
            provider = ""
            model = ""
            fallback_reason = ""
            for event in stream_answer(
                payload["context"],
                payload["question"],
                ollama_model=request.ollama_model,
                openrouter_model=request.openrouter_model,
                confidence="high",
                force_provider=request.force_provider or "",
            ):
                if event.get("type") == "delta":
                    full_answer += event.get("text", "")
                elif event.get("type") == "meta":
                    provider = event.get("provider", provider)
                    model = event.get("model", model)
                    fallback_reason = event.get("fallback_reason", fallback_reason)
                elif event.get("type") == "done":
                    provider = event.get("provider", provider)
                    model = event.get("model", model)
                    continue
                yield stream_json_event(event)

            result["answer"] = full_answer.strip()
            result["provider"] = provider
            result["model"] = model
            result["confidence"] = "compare tool"
            result["fallback_reason"] = fallback_reason
            result["answer_time_ms"] = round((time.perf_counter() - started_at) * 1000)
            yield stream_json_event({
                "type": "compare_done",
                "result": result,
                "provider": provider,
                "model": model,
                "fallback_reason": fallback_reason,
            })
        except ValueError as e:
            yield stream_json_event({"type": "error", "message": str(e)})
        except Exception as e:
            print(f"Error in /compare/stream: {str(e)}")
            yield stream_json_event({"type": "error", "message": "Compare Tool streaming failed."})

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/summarize-page")
def summarize_page(request: PageSummaryRequest):
    started_at = time.perf_counter()
    try:
        _autodetect_provider(request)
        page_text = normalize_page_content(request.content or "")
        if len(page_text.strip()) < 20:
            return {
                "answer": "I could not find enough readable page content to summarize.",
                "provider": "none",
                "model": "",
                "suggestions": ["Ask about this page", "Refresh page content", "Try a shorter question"],
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000),
            }

        summary_type = (request.summary_type or "quick").lower().strip()
        summary_instructions = {
            "tldr": "Write a 1-2 sentence TLDR with only the most important point.",
            "takeaways": "List 4-6 key takeaways as concise bullets.",
            "detailed": "Write a structured summary with short headings and important details.",
            "quick": "Write a compact summary in 1 short paragraph plus 3 key bullets.",
        }
        instruction = summary_instructions.get(summary_type, summary_instructions["quick"])
        context = (
            "ACTIVE MODE: Website\n"
            "MODE: Website. Summarize only the current page content.\n\n"
            f"Page title: {request.title or 'Current page'}\n"
            f"Page URL: {request.url}\n\n"
            f"Website context:\n{page_text[:12000]}"
        )
        question = (
            f"{instruction}\n"
            "Use only the provided page context. Keep it clear, useful, and easy to scan."
        )

        llm_result = generate_answer(
            context=context,
            question=question,
            history=None,
            external_context=None,
            ollama_model=request.ollama_model,
            openrouter_model=request.openrouter_model,
            confidence="high",
            feedback_guidance="",
            force_provider=request.force_provider or "",
            concise_answer=(summary_type in ("quick", "tldr")),
            document_mode="website",
        )
        return {
            "answer": llm_result.get("answer") or "I could not summarize this page.",
            "provider": llm_result.get("provider", ""),
            "model": llm_result.get("model", ""),
            "suggestions": ["List key details", "Explain simply", "Make a chart"],
            "answer_time_ms": round((time.perf_counter() - started_at) * 1000),
        }
    except Exception as e:
        print(f"Error in /summarize-page: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to summarize page.")

@app.post("/cancel")
async def cancel_request(request: CancelRequest):
    event = cancellation_event(request.request_id)
    event.set()
    return {"cancelled": True, "request_id": request.request_id}

@app.post("/cleanup")
async def cleanup_collections(request: CleanupRequest):
    try:
        return delete_old_collections(request.max_age_days)
    except Exception as e:
        print(f"Error in /cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clean old collections.")

@app.post("/crawl")
async def crawl_and_index(request: CrawlRequest):
    try:
        max_pages = max(1, min(request.max_pages, 25))
        crawl_result = crawl_website(request.url, max_pages=max_pages)
        pages = crawl_result.get("pages", [])
        if not pages:
            return {"indexed": False, "reason": "no_pages", "site_url": site_key(request.url),
                "pages": 0, "errors": crawl_result.get("errors", []), "content_hash": ""}
        site_url = crawl_result["site_url"]
        index_result = process_and_store_pages(site_url, pages)
        return {**index_result, "site_url": site_url, "start_url": request.url, "errors": crawl_result.get("errors", [])}
    except Exception as e:
        print(f"Error in /crawl: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to crawl and index website.")

@app.post("/document/upload")
async def upload_document(request: DocumentUploadRequest):
    try:
        filename = safe_document_filename(request.filename)
        try:
            data = base64.b64decode(request.content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid uploaded file content.") from exc
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(data) > 12 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Upload is too large. Please use a file under 12 MB.")
        extracted_text = normalize_page_content(extract_document_text(filename, data))
        if len(extracted_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="I could not extract enough readable text from this document.")
        digest = hashlib.sha256(data).hexdigest()[:24]
        document_id = f"{digest}-{hashlib.sha256(filename.encode('utf-8')).hexdigest()[:8]}"
        document_url = document_collection_url(document_id)
        result = process_and_store_document(document_url, extracted_text, filename)
        return {
            "document_id": document_id, "document_url": document_url, "filename": filename,
            "content_hash": result.get("content_hash", content_hash(extracted_text)),
            "chunks": result.get("chunks", 0), "indexed": result.get("indexed", False),
            "reason": result.get("reason", ""), "text_chars": len(extracted_text),
            "extracted_text": extracted_text[:80000],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /document/upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded document.")


@app.post("/chat")
def chat_with_website(request: ChatRequest):
    started_at = time.perf_counter()
    cancel_event = cancellation_event(request.request_id)
    try:
        raise_if_cancelled(cancel_event)
        if not request.question or len(request.question.strip()) < 1:
            return {"answer": "Please ask a question about this page."}

        document_mode = chat_utils.normalize_document_mode(request.document_mode)
        document_url = document_collection_url(request.document_id) if request.document_id else ""

        if document_mode == "document" and not document_url:
            return document_chat.missing_document_response()

        latest_page_text = ""
        if document_mode != "document" and request.content:
            cleaned_text = normalize_page_content(request.content)
            latest_page_text = cleaned_text
            request_hash = content_hash(cleaned_text)
            if not request.content_hash or request.content_hash != request_hash:
                request.content_hash = request_hash
            schedule_page_index(request.url, cleaned_text, request.content_hash)
        elif document_mode != "document" and request.content_hash and not safe_is_content_current(request.url, request.content_hash):
            return {"answer": "This page content has changed. Please re-index the page and ask again.", "requires_index": True}

        should_cache_answer = (
            document_mode == "website"
            and not is_link_question(request.question)
            and not is_flowchart_request(request.question)
            and not request.history
        )

        if request.content_hash and should_cache_answer:
            cache_key = answer_cache_key(request.url, request.content_hash, request.question,
                request.ollama_model or OLLAMA_MODEL, request.openrouter_model or "",
                request.force_provider or "", request.concise_answer)
            cached_answer = get_cached_answer(cache_key)
            if cached_answer:
                cached_answer["cached"] = True
                cached_answer.setdefault("metrics", {})["answer_time_ms"] = round((time.perf_counter() - started_at) * 1000)
                observe_event("chat_cache_hit", {"request_id": request.request_id or "", "url": request.url,
                    "document_mode": document_mode, "question": request.question[:260],
                    "answer_time_ms": cached_answer["metrics"]["answer_time_ms"],
                    "provider": cached_answer.get("provider", ""), "model": cached_answer.get("model", ""), "cached_answer": True})
                return cached_answer

        rate_limit_key = f"{request.url}|{document_mode}|{request.document_id or ''}"
        if not rate_limit_chat(rate_limit_key):
            return {"answer": "Too many questions too quickly. Please wait a moment and try again.", "rate_limited": True}

        _autodetect_provider(request)

        flowchart_question = is_flowchart_request(request.question)
        scoped_history = chat_utils.mode_scoped_history(request.history, document_mode)
        scoped_memory = chat_utils.mode_scoped_conversation_memory(request.conversation_memory, document_mode)

        augmented_history = chat_utils.memory_augmented_history(scoped_history, scoped_memory)
        memory_summary = chat_utils.conversation_memory_summary(scoped_memory)

        retrieval_question = rewrite_follow_up_question(request.question, augmented_history)
        retrieval_started_at = time.perf_counter()
        raise_if_cancelled(cancel_event)
        n_results = 3 if request.concise_answer else 5

        retrieval, document_retrieval = chat_retrieval.retrieve_page_and_document_contexts(
            document_mode=document_mode, url=request.url, document_url=document_url,
            question=request.question, retrieval_question=retrieval_question,
            live_retrieval_question=retrieval_question, latest_page_text=latest_page_text,
            n_results=n_results,
            empty_retrieval=chat_utils.empty_retrieval, live_page_context=chat_utils.live_page_context,
            retrieve_context=safe_retrieve_context_with_sources, is_link_question=is_link_question,
        )
        retrieval_time_ms = round((time.perf_counter() - retrieval_started_at) * 1000)
        raise_if_cancelled(cancel_event)

        context_validation = chat_utils.validate_answer_context(retrieval, retrieval_question, document_mode,
            allow_empty=flowchart_question or document_mode == "document")
        document_context_validation = chat_utils.validate_answer_context(document_retrieval, retrieval_question,
            "document", allow_empty=document_mode == "website")

        website_context = retrieval["context"]
        document_context = document_retrieval["context"]
        context = chat_context.build_mode_context(document_mode, website_context, document_context, request.question, provider=request.force_provider)
        external_context = ""
        used_external_search = False
        retrieval_confidence = chat_context.retrieval_confidence_for_mode(document_mode, retrieval, document_retrieval, website_context, document_context)

        if document_mode == "document" and not document_context:
            return document_chat.empty_document_response(
                answer_time_ms=round((time.perf_counter() - started_at) * 1000),
                retrieval_time_ms=retrieval_time_ms, document_retrieval=document_retrieval, document_mode=document_mode)

        if document_mode == "website" and not flowchart_question:
            if website_chat.should_escalate_for_weak_context(context_validation=context_validation, retrieval_confidence=retrieval_confidence) \
               or website_chat.should_search_external(context=context, retrieval_question=retrieval_question,
                    retrieval_confidence=retrieval_confidence, is_general_knowledge_question=chat_utils.is_general_knowledge_question,
                    needs_external_search=needs_external_search):
                if not request.allow_external_search:
                    return website_chat.external_permission_response(
                        answer_time_ms=round((time.perf_counter() - started_at) * 1000),
                        retrieval_time_ms=retrieval_time_ms, context=context, retrieval=retrieval,
                        retrieval_question=retrieval_question, retrieval_confidence=retrieval_confidence)
                raise_if_cancelled(cancel_event)
                external_context = search_duckduckgo(request.question, max_results=5)
                used_external_search = bool(external_context)

        if document_mode == "website" and not flowchart_question and not context and not external_context and not memory_summary:
            return website_chat.empty_website_response(
                answer_time_ms=round((time.perf_counter() - started_at) * 1000),
                retrieval_time_ms=retrieval_time_ms, requires_index=not bool(request.content_hash))

        context = chat_context.with_memory_context(memory_summary, context)

        if not context:
            context = "No relevant information from the current page was retrieved."

        generation_started_at = time.perf_counter()
        raise_if_cancelled(cancel_event)
        llm_result = generate_answer(
            context, request.question, history=augmented_history, external_context=external_context or None,
            ollama_model=request.ollama_model, openrouter_model=request.openrouter_model,
            confidence=retrieval_confidence, feedback_guidance=feedback_guidance_for_url(request.url),
            force_provider=request.force_provider or "",
            concise_answer=request.concise_answer, cancel_event=cancel_event, document_mode=document_mode)
        raise_if_cancelled(cancel_event)
        generation_time_ms = round((time.perf_counter() - generation_started_at) * 1000)
        answer = llm_result["answer"]

        external_notice = "I could not find enough information on the current page, so I used external DuckDuckGo search results."
        if used_external_search and external_notice.lower() not in answer.lower():
            answer = f"{external_notice}\n\n{answer}"
        elif document_mode == "website" and not flowchart_question and retrieval_confidence in ("low", "medium") and "I found limited information on this page." not in answer:
            answer = f"I found limited information on this page.\n\n{answer}"

        suggestions = chat_response.suggestions_for_mode(document_mode, request.question, request.url, chat_utils.fast_follow_up_suggestions)
        combined_sources = chat_response.combine_sources(retrieval.get("sources", []), document_retrieval.get("sources", []))
        token_metrics = chat_response.token_cost_metrics(context, request.question, answer, llm_result["provider"], llm_result["model"])
        response_payload = chat_response.build_chat_response_payload(
            answer=answer, combined_sources=combined_sources, suggestions=suggestions,
            used_external_search=used_external_search, retrieval_confidence=retrieval_confidence,
            llm_result=llm_result, answer_time_ms=round((time.perf_counter() - started_at) * 1000),
            generation_time_ms=generation_time_ms, retrieval_time_ms=retrieval_time_ms,
            retrieval=retrieval, document_retrieval=document_retrieval, context=context,
            context_validation=context_validation, document_context_validation=document_context_validation,
            retrieval_question=retrieval_question, original_question=request.question,
            concise_answer=request.concise_answer, document_mode=document_mode, token_metrics=token_metrics)

        observe_event("chat", chat_response.build_chat_observability_payload(
            request_id=request.request_id or "", url=request.url, document_mode=document_mode,
            question=request.question, response_payload=response_payload,
            retrieval_time_ms=retrieval_time_ms, generation_time_ms=generation_time_ms,
            retrieval=retrieval, retrieval_question=retrieval_question, retrieval_confidence=retrieval_confidence,
            used_external_search=used_external_search, context_validation=context_validation,
            document_context_validation=document_context_validation, token_metrics=token_metrics))

        if request.content_hash and should_cache_answer:
            store_cached_answer(cache_key, response_payload.copy())

        print("Chat metrics:", {"provider": response_payload["provider"], "model": response_payload["model"],
            "answer_time_ms": response_payload["metrics"]["answer_time_ms"],
            "context_chars": response_payload["metrics"]["context_chars"],
            "confidence": response_payload["confidence"],
            "retrieval_mode": response_payload["metrics"]["retrieval_mode"],
            "reranked": response_payload["metrics"]["reranked"],
            "fallback_reason": response_payload["fallback_reason"]})

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to answer the question.")
    finally:
        if request.request_id:
            cancel_events.pop(request.request_id, None)


@app.post("/chat/stream")
def stream_chat_with_website(request: ChatRequest):
    started_at = time.perf_counter()
    cancel_event = cancellation_event(request.request_id)

    def events():
        try:
            raise_if_cancelled(cancel_event)
            if not request.question or len(request.question.strip()) < 1:
                yield stream_json_event({"type": "delta", "text": "Please ask a question about this page."})
                yield stream_json_event({"type": "done", "provider": "none", "model": ""})
                return

            document_mode = chat_utils.normalize_document_mode(request.document_mode)
            if document_mode != "website":
                yield stream_json_event({"type": "error", "message": "Streaming is enabled for website chat only. Document mode uses regular chat; compare mode uses the dedicated /compare endpoint."})
                return

            latest_page_text = ""
            if request.content:
                latest_page_text = normalize_page_content(request.content)
                request_hash = content_hash(latest_page_text)
                if not request.content_hash or request.content_hash != request_hash:
                    request.content_hash = request_hash
            schedule_page_index(request.url, latest_page_text, request.content_hash)

            _autodetect_provider(request)

            flowchart_question = is_flowchart_request(request.question)
            scoped_history = chat_utils.mode_scoped_history(request.history, document_mode)
            scoped_memory = chat_utils.mode_scoped_conversation_memory(request.conversation_memory, document_mode)
            augmented_history = chat_utils.memory_augmented_history(scoped_history, scoped_memory)
            memory_summary = chat_utils.conversation_memory_summary(scoped_memory)
            retrieval_question = rewrite_follow_up_question(request.question, augmented_history)
            retrieval_started_at = time.perf_counter()
            retrieval = chat_retrieval.retrieve_website_context(
                document_mode=document_mode, url=request.url, question=request.question,
                retrieval_question=retrieval_question, live_retrieval_question=request.question,
                latest_page_text=latest_page_text,
                n_results=3 if request.concise_answer else 5,
                empty_retrieval=chat_utils.empty_retrieval, live_page_context=chat_utils.live_page_context,
                retrieve_context=safe_retrieve_context_with_sources, is_link_question=is_link_question)

            retrieval_time_ms = round((time.perf_counter() - retrieval_started_at) * 1000)
            context_validation = chat_utils.validate_answer_context(retrieval, retrieval_question, document_mode,
                allow_empty=flowchart_question)
            context = retrieval.get("context", "")
            retrieval_confidence = retrieval.get("confidence", "high")
            external_context = ""
            used_external_search = False

            if document_mode == "website" and not flowchart_question:
                if website_chat.should_escalate_for_weak_context(context_validation=context_validation, retrieval_confidence=retrieval_confidence) \
                   or website_chat.should_search_external(context=context, retrieval_question=retrieval_question,
                        retrieval_confidence=retrieval_confidence, is_general_knowledge_question=chat_utils.is_general_knowledge_question,
                        needs_external_search=lambda _ctx, _q: False):
                    if not request.allow_external_search:
                        yield stream_json_event({"type": "external_required", "confidence": retrieval_confidence,
                            "sources": retrieval.get("sources", []),
                            "suggestions": ["Use DuckDuckGo", "Ask about this page", "Summarize this page"],
                            "metrics": {"answer_time_ms": round((time.perf_counter() - started_at) * 1000),
                                "retrieval_time_ms": retrieval_time_ms,
                                "context_chars": retrieval.get("context_chars", len(context)),
                                "selected_chunks": retrieval.get("selected_chunks", 0),
                                "confidence": retrieval_confidence,
                                "retrieval_mode": retrieval.get("retrieval_mode", ""),
                                "external_permission_required": True}})
                        return
                    external_context = search_duckduckgo(request.question, max_results=5)
                    used_external_search = bool(external_context)

            if not flowchart_question and not context and not external_context and not memory_summary:
                yield stream_json_event({"type": "delta", "text": "I couldn't find relevant information on this page or from external search."})
                yield stream_json_event({"type": "done", "provider": "none", "model": ""})
                return

            context = chat_context.with_memory_context(memory_summary, context)
            if not context:
                context = "No relevant information from the current page was retrieved."

            generation_started_at = time.perf_counter()
            full_answer = ""
            provider = "none"
            model = ""
            fallback_reason = ""

            yield stream_json_event({"type": "context", "sources": retrieval.get("sources", []),
                "confidence": retrieval_confidence, "used_external_search": used_external_search,
                "retrieval_mode": retrieval.get("retrieval_mode", ""), "context_validation": context_validation,
                "metrics": {"retrieval_time_ms": retrieval_time_ms,
                    "context_chars": retrieval.get("context_chars", len(context)),
                    "selected_chunks": retrieval.get("selected_chunks", 0),
                    "source_count": len(retrieval.get("sources", [])),
                    "context_validation": context_validation}})

            if is_flowchart_request(request.question):
                llm_result = generate_answer(context, request.question, history=augmented_history,
                    external_context=external_context or None, ollama_model=request.ollama_model,
                    openrouter_model=request.openrouter_model, confidence=retrieval_confidence,
                    feedback_guidance=feedback_guidance_for_url(request.url),
                    force_provider=request.force_provider or "",
                    concise_answer=request.concise_answer, cancel_event=cancel_event, document_mode=document_mode)
                raise_if_cancelled(cancel_event)
                provider = llm_result.get("provider", provider)
                model = llm_result.get("model", model)
                fallback_reason = llm_result.get("fallback_reason", fallback_reason)
                full_answer = llm_result.get("answer", "")
                if full_answer:
                    yield stream_json_event({"type": "meta", "provider": provider, "model": model, "fallback_reason": fallback_reason})
                    yield stream_json_event({"type": "delta", "text": full_answer})
                generation_time_ms = round((time.perf_counter() - generation_started_at) * 1000)
                answer_time_ms = round((time.perf_counter() - started_at) * 1000)
                token_metrics = chat_response.token_cost_metrics(context, request.question, full_answer, provider, model)
                observe_event("chat_stream", chat_response.build_stream_observability_payload(
                    request_id=request.request_id or "", url=request.url, document_mode=document_mode,
                    question=request.question, answer_time_ms=answer_time_ms, retrieval_time_ms=retrieval_time_ms,
                    generation_time_ms=generation_time_ms, provider=provider, model=model, retrieval=retrieval,
                    context=context, retrieval_question=retrieval_question, retrieval_confidence=retrieval_confidence,
                    used_external_search=used_external_search, context_validation=context_validation,
                    token_metrics=token_metrics, fallback_reason=fallback_reason))
                suggestions = chat_response.suggestions_for_mode(document_mode, request.question, request.url, chat_utils.fast_follow_up_suggestions)
                yield stream_json_event(chat_response.build_stream_done_event(provider=provider, model=model,
                    retrieval=retrieval, suggestions=suggestions, used_external_search=used_external_search,
                    retrieval_confidence=retrieval_confidence, fallback_reason=fallback_reason,
                    answer_time_ms=answer_time_ms, generation_time_ms=generation_time_ms,
                    retrieval_time_ms=retrieval_time_ms, context=context,
                    context_validation=context_validation, token_metrics=token_metrics))
                return

            for event in stream_answer(context, request.question, history=augmented_history,
                    external_context=external_context or None, ollama_model=request.ollama_model,
                    openrouter_model=request.openrouter_model, confidence=retrieval_confidence,
                    feedback_guidance=feedback_guidance_for_url(request.url),
                    force_provider=request.force_provider or "", concise_answer=request.concise_answer,
                    cancel_event=cancel_event):
                raise_if_cancelled(cancel_event)
                if event.get("type") == "delta":
                    full_answer += event.get("text", "")
                elif event.get("type") == "meta":
                    provider = event.get("provider", provider)
                    model = event.get("model", model)
                    fallback_reason = event.get("fallback_reason", fallback_reason)
                elif event.get("type") == "done":
                    provider = event.get("provider", provider)
                    model = event.get("model", model)
                    generation_time_ms = round((time.perf_counter() - generation_started_at) * 1000)
                    answer_time_ms = round((time.perf_counter() - started_at) * 1000)
                    token_metrics = chat_response.token_cost_metrics(context, request.question, full_answer, provider, model)
                    observe_event("chat_stream", chat_response.build_stream_observability_payload(
                        request_id=request.request_id or "", url=request.url, document_mode=document_mode,
                        question=request.question, answer_time_ms=answer_time_ms, retrieval_time_ms=retrieval_time_ms,
                        generation_time_ms=generation_time_ms, provider=provider, model=model, retrieval=retrieval,
                        context=context, retrieval_question=retrieval_question, retrieval_confidence=retrieval_confidence,
                        used_external_search=used_external_search, context_validation=context_validation,
                        token_metrics=token_metrics, fallback_reason=fallback_reason))
                    suggestions = chat_response.suggestions_for_mode(document_mode, request.question, request.url, chat_utils.fast_follow_up_suggestions)
                    yield stream_json_event(chat_response.build_stream_done_event(provider=provider, model=model,
                        retrieval=retrieval, suggestions=suggestions, used_external_search=used_external_search,
                        retrieval_confidence=retrieval_confidence, fallback_reason=fallback_reason,
                        answer_time_ms=answer_time_ms, generation_time_ms=generation_time_ms,
                        retrieval_time_ms=retrieval_time_ms, context=context,
                        context_validation=context_validation, token_metrics=token_metrics))
                    return
                yield stream_json_event(event)

        except HTTPException as exc:
            yield stream_json_event({"type": "error", "message": exc.detail})
        except Exception as exc:
            print(f"Error in /chat/stream: {str(exc)}")
            yield stream_json_event({"type": "error", "message": "Failed to stream the answer."})
        finally:
            if request.request_id:
                cancel_events.pop(request.request_id, None)

    return StreamingResponse(events(), media_type="application/x-ndjson")


class WebpageContentRequest(BaseModel):
    url: str

@app.post("/webpage-content")
async def fetch_webpage_content(request: WebpageContentRequest):
    import urllib.request
    import urllib.error
    import re as _re

    target_url = (request.url or "").strip()
    if not target_url:
        raise HTTPException(status_code=400, detail="URL is required.")
    if not target_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Only http and https URLs are supported.")
    try:
        req = urllib.request.Request(target_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; WebsiteChatbot/1.0)",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = "utf-8"
            content_type = resp.headers.get("Content-Type", "")
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
            raw_html = decode_bytes(resp.read(), charset)
        text = clean_html_content(raw_html)
        text = _re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text.strip()) < 20:
            raise HTTPException(status_code=422, detail="Could not extract enough readable text from that URL.")
        return {"url": target_url, "text": text[:80000], "chars": len(text)}
    except HTTPException:
        raise
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"The target page returned HTTP {e.code}.")
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach that URL: {str(e.reason)}")
    except Exception as e:
        print(f"Error in /webpage-content: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webpage content.")


class SafetyRequest(BaseModel):
    url: str
    content: str

@app.post("/safety-check")
async def check_safety(request: SafetyRequest):
    try:
        cleaned_text = normalize_page_content(request.content)
        result = analyze_website_safety(request.url, cleaned_text)
        return result
    except Exception as e:
        print(f"Error in /safety-check: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze website safety.")


@app.post("/chart")
def create_chart(request: ChartRequest):
    """Generate a data chart grounded in live page/document content.
    Supported types: bar, horizontal_bar, line, pie, donut, radar.
    Returns ok=True and answer=raw JSON string when successful.
    """
    started_at = time.perf_counter()
    try:
        document_mode = chat_utils.normalize_document_mode(request.document_mode)
        document_url = document_collection_url(request.document_id) if request.document_id else ""
        _autodetect_provider(request)

        if document_mode == "compare":
            return {"ok": False, "error": "Compare mode uses the dedicated Compare Tool. Run /compare instead of the chart endpoint.",
                "answer": "", "provider": "", "model": "", "sources": [], "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        latest_page_text = ""
        if document_mode != "document" and request.content:
            latest_page_text = normalize_page_content(request.content)
            request.content_hash = request.content_hash or content_hash(latest_page_text)
            schedule_page_index(request.url, latest_page_text, request.content_hash)

        retrieval_question = request.question or "key statistics, numbers, metrics, data, values, percentages"

        if document_mode == "document" and document_url:
            retrieval = safe_retrieve_context_with_sources(document_url, retrieval_question, n_results=8)
        else:
            if latest_page_text:
                live_context = chat_utils.live_page_context(
                    retrieval_question,
                    latest_page_text,
                    request.url,
                    max_chars=9000,
                )
                stored = safe_retrieve_context_with_sources(request.url, retrieval_question, n_results=5)
                combined_ctx = "\n\n".join(filter(None, [live_context, stored.get("context", "")]))
                retrieval = {**stored, "context": combined_ctx}
            else:
                retrieval = safe_retrieve_context_with_sources(request.url, retrieval_question, n_results=8)

        context = retrieval.get("context", "").strip()
        sources = retrieval.get("sources", [])

        if not context:
            return {"ok": False, "error": "I couldn't find enough data on this page to build a chart. Try indexing the page first.",
                "answer": "", "provider": "", "model": "", "sources": [], "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        prompt = chart_tool.build_chart_prompt(context, request.question, document_mode)
        llm_result = generate_answer(
            context=context,
            question=request.question,
            history=None,
            ollama_model=request.ollama_model,
            openrouter_model=request.openrouter_model,
            force_provider=request.force_provider or "",
            concise_answer=False,
            document_mode=document_mode,
            feedback_guidance=prompt,
        )

        raw = str(llm_result.get("answer") or "").strip()
        parsed = chart_tool.extract_chart_json(raw)
        if parsed is None:
            return {"ok": False,
                "warning": "The model did not return chart JSON. This usually means the context did not contain enough numeric data for a chart.",
                "answer": raw, "provider": llm_result.get("provider", ""), "model": llm_result.get("model", ""),
                "sources": sources, "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}
        valid, validation_error = chart_tool.validate_chart_payload(parsed or {})

        if not valid:
            return {"ok": False,
                "warning": validation_error or "The model produced an incomplete chart. Try rephrasing or ask about a page with clearer numeric data.",
                "answer": raw, "provider": llm_result.get("provider", ""), "model": llm_result.get("model", ""),
                "sources": sources, "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        chart_answer = chart_tool.chart_answer_from_data(parsed)
        return {"ok": True, "answer": chart_answer, "provider": llm_result.get("provider", ""),
            "model": llm_result.get("model", ""), "sources": sources, "mode": document_mode,
            "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

    except Exception as exc:
        print(f"Error in /chart: {exc}")
        return {"ok": False, "error": "Chart generation failed due to an internal error.",
            "answer": "", "provider": "", "model": "", "sources": [], "mode": request.document_mode,
            "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}


@app.post("/flowchart")
def create_flowchart(request: FlowchartRequest):
    """Dedicated endpoint for flowchart generation, isolated from /chat
    rate limits and caching. Retrieves page context and uses generate_answer()
    with flowchart detection active.
    """
    started_at = time.perf_counter()
    try:
        document_mode = chat_utils.normalize_document_mode(request.document_mode)
        document_url = document_collection_url(request.document_id) if request.document_id else ""
        _autodetect_provider(request)

        if document_mode == "compare":
            return {"ok": False, "error": "Compare mode uses the dedicated Compare Tool. Run /compare instead of the flowchart endpoint.",
                "answer": "", "provider": "", "model": "", "sources": [], "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        latest_page_text = ""
        if document_mode != "document" and request.content:
            latest_page_text = normalize_page_content(request.content)
            request.content_hash = request.content_hash or content_hash(latest_page_text)
            schedule_page_index(request.url, latest_page_text, request.content_hash)

        if document_mode == "document" and document_url:
            retrieval = safe_retrieve_context_with_sources(document_url, request.question, n_results=8)
        else:
            if latest_page_text:
                live_context = chat_utils.live_page_context(
                    request.question,
                    latest_page_text,
                    request.url,
                    max_chars=9000,
                )
                stored = safe_retrieve_context_with_sources(request.url, request.question, n_results=5)
                combined_ctx = "\n\n".join(filter(None, [live_context, stored.get("context", "")]))
                retrieval = {**stored, "context": combined_ctx}
            else:
                retrieval = safe_retrieve_context_with_sources(request.url, request.question, n_results=8)

        context = retrieval.get("context", "").strip()
        sources = retrieval.get("sources", [])

        if not context:
            return {"ok": False, "error": "I couldn't find enough content on this page to build a flowchart. Try indexing the page first.",
                "answer": "", "provider": "", "model": "", "sources": [], "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        scoped_history = chat_utils.mode_scoped_history(request.history, document_mode)
        llm_result = generate_answer(context=context, question=request.question, history=scoped_history,
            ollama_model=request.ollama_model, openrouter_model=request.openrouter_model,
            force_provider=request.force_provider or "", concise_answer=False, document_mode=document_mode)

        answer = (llm_result.get("answer") or "").strip()
        if not answer:
            return {"ok": False, "error": "The model returned an empty diagram. Try rephrasing the request.",
                "answer": "", "provider": llm_result.get("provider", ""), "model": llm_result.get("model", ""),
                "sources": sources, "mode": document_mode,
                "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

        return {"ok": True, "answer": answer, "provider": llm_result.get("provider", ""),
            "model": llm_result.get("model", ""), "sources": sources, "mode": document_mode,
            "fallback_reason": llm_result.get("fallback_reason", ""),
            "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}

    except Exception as exc:
        print(f"Error in /flowchart: {exc}")
        return {"ok": False, "error": "Flowchart generation failed due to an internal error.",
            "answer": "", "provider": "", "model": "", "sources": [], "mode": request.document_mode,
            "answer_time_ms": round((time.perf_counter() - started_at) * 1000)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
