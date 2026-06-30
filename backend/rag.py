import os
import hashlib
import math
import re
import time
from typing import Optional
from collections import Counter, OrderedDict
import chromadb
from chromadb.utils import embedding_functions

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
embedding_function: Optional[embedding_functions.SentenceTransformerEmbeddingFunction] = None
reranker_model = None
reranker_load_failed = False
ADD_BATCH_SIZE = 64
MAX_COLLECTIONS = int(os.getenv("CHROMA_MAX_COLLECTIONS", "150"))
BOILERPLATE_LINE_THRESHOLD = int(os.getenv("BOILERPLATE_LINE_THRESHOLD", "4"))
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "true").lower() in ("1", "true", "yes", "on")
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-base")
HYBRID_BM25_CANDIDATES = int(os.getenv("HYBRID_BM25_CANDIDATES", "20"))
HYBRID_VECTOR_CANDIDATES = int(os.getenv("HYBRID_VECTOR_CANDIDATES", "12"))
HYBRID_RERANK_CANDIDATES = int(os.getenv("HYBRID_RERANK_CANDIDATES", "12"))
RETRIEVAL_CACHE_MAX_ITEMS = int(os.getenv("RETRIEVAL_CACHE_MAX_ITEMS", "200"))
retrieval_cache: OrderedDict[str, dict] = OrderedDict()
_collection_meta_cache: OrderedDict[str, dict] = OrderedDict()

# ── In-memory BM25 document cache ────────────────────────────────────────────
_bm25_doc_cache: dict[str, dict] = {}
BM25_CACHE_MAX_COLLECTIONS = 50
COLLECTION_META_CACHE_MAX_ITEMS = 150

# Context compression limits — tighter for normal chat, full for complex modes
NORMAL_CONTEXT_MAX_CHARS  = 2400
COMPLEX_CONTEXT_MAX_CHARS = 3200

LINK_QUESTION_TERMS = {
    "link", "links", "url", "urls", "href", "hyperlink", "anchor",
    "redirect", "button", "contact", "pricing", "signup", "sign",
    "login", "download", "apply", "register",
}

DOCUMENT_SECTION_ALIASES = {
    "summary": "Summary",
    "professional_summary": "Summary",
    "profile": "Summary",
    "objective": "Summary",
    "skills": "Skills",
    "technical_skills": "Skills",
    "core_skills": "Skills",
    "key_skills": "Skills",
    "competencies": "Skills",
    "experience": "Experience",
    "work_experience": "Experience",
    "professional_experience": "Experience",
    "employment": "Experience",
    "employment_history": "Experience",
    "work_history": "Experience",
    "education": "Education",
    "academic_background": "Education",
    "academics": "Education",
    "qualification": "Education",
    "qualifications": "Qualifications",
    "projects": "Projects",
    "project_experience": "Projects",
    "certifications": "Certifications",
    "licenses": "Certifications",
    "responsibilities": "Responsibilities",
    "roles_responsibilities": "Responsibilities",
    "requirements": "Requirements",
    "required_skills": "Requirements",
    "required_qualifications": "Qualifications",
    "preferred_qualifications": "Qualifications",
    "benefits": "Benefits",
    "introduction": "Introduction",
    "background": "Background",
    "findings": "Findings",
    "conclusion": "Conclusion",
}

SECTION_QUERY_TERMS = {
    "skills": {"skill", "skills", "technology", "technologies", "tool", "tools", "stack", "competenc"},
    "education": {"degree", "education", "college", "university", "school", "academic", "qualification", "qualifications"},
    "experience": {"experience", "work", "worked", "employment", "history", "job", "role", "roles", "career"},
    "projects": {"project", "projects", "portfolio"},
    "certifications": {"certification", "certifications", "certificate", "license", "licenses"},
    "responsibilities": {"responsibility", "responsibilities", "duties", "day", "tasks"},
    "requirements": {"requirement", "requirements", "required", "must", "need", "needs", "mandatory"},
    "qualifications": {"qualification", "qualifications", "eligible", "eligibility", "preferred"},
    "benefits": {"benefit", "benefits", "perks", "compensation"},
    "summary": {"summary", "overview", "about", "profile"},
}


def _collection_name(collection) -> str:
    return getattr(collection, "name", "")


def _is_chroma_storage_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "hnsw segment reader" in message
        or "nothing found on disk" in message
        or "error executing plan" in message
    )


def _is_missing_collection_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "collection" in message and "does not exist" in message


def _delete_collection(name: str) -> bool:
    if not name:
        return False
    _bm25_doc_cache.pop(name, None)
    _collection_meta_cache.pop(name, None)
    try:
        chroma_client.delete_collection(name)
        retrieval_cache.clear()
        print(f"Deleted broken Chroma collection: {name}")
        return True
    except Exception as exc:
        print(f"Failed to delete Chroma collection {name}: {exc}")
        return False


def _repair_collection_after_error(collection, exc: Exception) -> bool:
    if not _is_chroma_storage_error(exc):
        return False
    name = _collection_name(collection)
    if not name:
        return False
    return _delete_collection(name)


def _collection_count(collection) -> int:
    try:
        return collection.count()
    except Exception as exc:
        if _is_missing_collection_error(exc):
            return 0
        if _repair_collection_after_error(collection, exc):
            return 0
        raise


def get_embedding_function():
    global embedding_function
    if embedding_function is None:
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME,
            local_files_only=True,
        )
    return embedding_function


def get_reranker_model():
    global reranker_model, reranker_load_failed
    if not ENABLE_RERANKER or reranker_load_failed:
        return None
    if reranker_model is not None:
        return reranker_model
    try:
        from sentence_transformers import CrossEncoder
        reranker_model = CrossEncoder(RERANKER_MODEL_NAME, device="cpu", local_files_only=True)
        return reranker_model
    except Exception as exc:
        reranker_load_failed = True
        print(f"Reranker unavailable, using RRF score only: {exc}")
        return None


def _sanitize_collection_name(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return f"url_{digest}"


def content_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_collection(url: str):
    safe_name = _sanitize_collection_name(url)
    return chroma_client.get_or_create_collection(
        name=safe_name,
        embedding_function=get_embedding_function()
    )


def _get_collection_name(url: str) -> str:
    return _sanitize_collection_name(url)


def _chunk_plain_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    sections = _split_into_sections(text)
    chunks = []
    for section in sections:
        chunks.extend(_chunk_section(section, chunk_size, overlap))
    return _dedupe_chunks(chunks)


def _split_into_sections(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    if sum(1 for line in lines if line) < 3:
        return [text]
    sections = []
    current = []
    for line in lines:
        if not line:
            if current:
                current.append("")
            continue
        is_heading = (
            len(line) <= 90
            and not line.endswith((".", ",", ";", ":"))
            and (line.istitle() or line.isupper() or re.match(r"^#{1,6}\s+", line))
        )
        if is_heading and current:
            section = "\n".join(current).strip()
            if section:
                sections.append(section)
            current = [line]
        else:
            current.append(line)
    if current:
        section = "\n".join(current).strip()
        if section:
            sections.append(section)
    return sections or [text]


def _chunk_section(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    chunks = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            chunks.append(current)
            current = current[-overlap:].strip()
        if len(sentence) > chunk_size:
            for start in range(0, len(sentence), chunk_size - overlap):
                chunks.append(sentence[start:start + chunk_size])
            current = ""
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def _chunk_fingerprint(text: str) -> str:
    normalized = re.sub(r"\W+", " ", text.lower()).strip()
    return normalized[:900]


def _dedupe_chunks(chunks: list[str]) -> list[str]:
    unique = []
    seen = set()
    for chunk in chunks:
        cleaned = " ".join(chunk.split())
        if len(cleaned) < 30:
            continue
        fingerprint = _chunk_fingerprint(cleaned)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(cleaned)
    return unique


def remove_repeated_boilerplate(text: str) -> str:
    if "\n\nPage links:\n" in text:
        page_text, link_section = text.split("\n\nPage links:\n", 1)
    else:
        page_text, link_section = text, ""
    raw_lines = [line.strip() for line in page_text.splitlines()]
    normalized_lines = [
        re.sub(r"\W+", " ", line.lower()).strip()
        for line in raw_lines if line.strip()
    ]
    counts = Counter(line for line in normalized_lines if len(line) > 15)
    kept = []
    for line in raw_lines:
        normalized = re.sub(r"\W+", " ", line.lower()).strip()
        if counts.get(normalized, 0) >= BOILERPLATE_LINE_THRESHOLD:
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    if link_section:
        return f"{cleaned}\n\nPage links:\n{link_section}".strip()
    return cleaned


def _chunk_link_section(link_section: str, links_per_chunk: int = 20) -> list[str]:
    entries = [e.strip() for e in re.split(r"\n\s*\n", link_section) if e.strip()]
    chunks = []
    for start in range(0, len(entries), links_per_chunk):
        chunk = "\n\n".join(entries[start:start + links_per_chunk])
        chunks.append(f"Page links:\n{chunk}")
    return chunks


def _normalize_heading(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", heading.lower()).strip("_")


def _canonical_section_heading(heading: str) -> tuple[str, str]:
    normalized = _normalize_heading(re.sub(r"^#{1,6}\s+", "", heading).strip())
    canonical = DOCUMENT_SECTION_ALIASES.get(normalized)
    if canonical:
        return canonical, _normalize_heading(canonical)
    cleaned = " ".join(re.sub(r"^#{1,6}\s+", "", heading).strip().split())
    return cleaned or "General", normalized or "general"


def _looks_like_document_heading(line: str) -> bool:
    cleaned = re.sub(r"^#{1,6}\s+", "", line).strip()
    normalized = _normalize_heading(cleaned)
    if normalized in DOCUMENT_SECTION_ALIASES:
        return True
    return (
        len(cleaned) <= 90
        and not cleaned.endswith((".", ",", ";", ":"))
        and (cleaned.istitle() or cleaned.isupper() or re.match(r"^#{1,6}\s+", line))
    )


def _split_into_sections_with_metadata(text: str) -> list[dict]:
    lines = [line.strip() for line in text.splitlines()]
    if sum(1 for line in lines if line) < 3:
        return [{"heading": "General", "normalized_heading": "general", "text": text}]
    
    sections = []
    current_heading = "General"
    current_text = []
    
    for line in lines:
        if not line:
            if current_text:
                current_text.append("")
            continue
            
        is_heading = _looks_like_document_heading(line)
        
        if is_heading:
            if current_text:
                section_text = "\n".join(current_text).strip()
                if section_text:
                    heading, normalized_heading = _canonical_section_heading(current_heading)
                    sections.append({
                        "heading": heading,
                        "normalized_heading": normalized_heading,
                        "text": section_text
                    })
            current_heading = line
            current_text = []
        else:
            current_text.append(line)
            
    if current_text:
        section_text = "\n".join(current_text).strip()
        if section_text:
            heading, normalized_heading = _canonical_section_heading(current_heading)
            sections.append({
                "heading": heading,
                "normalized_heading": normalized_heading,
                "text": section_text
            })
            
    return sections or [{"heading": "General", "normalized_heading": "general", "text": text}]


def chunk_document_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[dict]:
    text = remove_repeated_boilerplate(text)
    sections = _split_into_sections_with_metadata(text)
    chunks = []
    for sec in sections:
        raw_chunks = _chunk_section(sec["text"], chunk_size, overlap)
        for rc in raw_chunks:
            chunks.append({
                "text": rc,
                "heading": sec["heading"],
                "normalized_heading": sec["normalized_heading"]
            })
    
    unique = []
    seen = set()
    for chunk in chunks:
        cleaned = " ".join(chunk["text"].split())
        if len(cleaned) < 30:
            continue
        fingerprint = _chunk_fingerprint(cleaned)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        chunk["text"] = cleaned
        unique.append(chunk)
    return unique


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    text = remove_repeated_boilerplate(text)
    if "\n\nPage links:\n" not in text:
        return _chunk_plain_text(text, chunk_size, overlap)
    page_text, link_section = text.split("\n\nPage links:\n", 1)
    chunks = _chunk_plain_text(page_text, chunk_size, overlap)
    chunks.extend(_chunk_link_section(link_section))
    return _dedupe_chunks(chunks)


def _set_collection_meta_cache(name: str, content_hash_val: str, chunk_count: int) -> None:
    if not name:
        return
    _collection_meta_cache[name] = {"hash": content_hash_val, "count": chunk_count}
    _collection_meta_cache.move_to_end(name)
    while len(_collection_meta_cache) > COLLECTION_META_CACHE_MAX_ITEMS:
        _collection_meta_cache.popitem(last=False)


def _stored_content_hash(collection, use_cache: bool = True) -> str:
    name = _collection_name(collection)
    if use_cache and name:
        cached = _collection_meta_cache.get(name)
        if cached is not None:
            _collection_meta_cache.move_to_end(name)
            return cached.get("hash", "")
    if _collection_count(collection) == 0:
        if name:
            _set_collection_meta_cache(name, "", 0)
        return ""
    try:
        result = collection.get(limit=1, include=["metadatas"])
    except Exception as exc:
        if _is_missing_collection_error(exc):
            return ""
        if _repair_collection_after_error(collection, exc):
            return ""
        raise
    metadatas = result.get("metadatas") or []
    if not metadatas:
        if name:
            _set_collection_meta_cache(name, "", _collection_count(collection))
        return ""
    stored_hash = metadatas[0].get("content_hash", "")
    if name:
        _set_collection_meta_cache(name, stored_hash, _collection_count(collection))
    return stored_hash


def _collection_cache_marker(collection, collection_count: int | None = None) -> str:
    stored_hash = _stored_content_hash(collection)
    if stored_hash:
        return stored_hash
    if collection_count is None:
        collection_count = _collection_count(collection)
    return str(collection_count)


def get_page_cache_status(url: str, text_hash: str = "") -> dict:
    collection = get_collection(url)
    stored_hash = _stored_content_hash(collection)
    chunk_count = _collection_count(collection)
    return {
        "url": url,
        "collection": _get_collection_name(url),
        "exists": chunk_count > 0,
        "chunks": chunk_count,
        "content_hash": stored_hash,
        "current": bool(text_hash and stored_hash == text_hash),
    }


def get_collection_stats(url: str) -> dict:
    return get_page_cache_status(url)


def batch_embed_chunks(collection, chunks: list[str], metadatas: list[dict], ids: list[str], batch_size: int = ADD_BATCH_SIZE):
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            documents=chunks[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end]
        )


def prune_collection_count(max_collections: int = MAX_COLLECTIONS) -> dict:
    url_collections = []
    for collection_info in chroma_client.list_collections():
        name = getattr(collection_info, "name", collection_info)
        if not name.startswith("url_"):
            continue
        collection = chroma_client.get_collection(name=name, embedding_function=get_embedding_function())
        indexed_at = 0
        if _collection_count(collection) > 0:
            try:
                result = collection.get(limit=1, include=["metadatas"])
            except Exception as exc:
                if _repair_collection_after_error(collection, exc):
                    continue
                raise
            metadatas = result.get("metadatas") or []
            indexed_at = metadatas[0].get("indexed_at", 0) if metadatas else 0
        url_collections.append((indexed_at, name))
    deleted = []
    overflow = max(0, len(url_collections) - max_collections)
    for _, name in sorted(url_collections)[:overflow]:
        if _delete_collection(name):
            deleted.append(name)
    return {"deleted": deleted, "max_collections": max_collections}


def _source_prefixed_chunk(chunk: str, source_url: str, title: str = "") -> str:
    title_line = f"Title: {title}\n" if title else ""
    return f"Source: {source_url}\n{title_line}{chunk}"


def _invalidate_bm25_cache(collection_name: str) -> None:
    _bm25_doc_cache.pop(collection_name, None)
    _collection_meta_cache.pop(collection_name, None)


def _get_cached_documents(collection, content_hash_val: str) -> Optional[list[str]]:
    name = _collection_name(collection)
    cached = _bm25_doc_cache.get(name)
    if cached and cached.get("hash") == content_hash_val:
        return cached["documents"]
    return None


def _set_cached_documents(collection, content_hash_val: str, documents: list[str]) -> None:
    name = _collection_name(collection)
    if len(_bm25_doc_cache) >= BM25_CACHE_MAX_COLLECTIONS and name not in _bm25_doc_cache:
        oldest = next(iter(_bm25_doc_cache))
        _bm25_doc_cache.pop(oldest, None)
    document_tokens = [_tokenize(d) for d in documents]
    avgdl = sum(len(t) for t in document_tokens) / max(len(document_tokens), 1)
    doc_freq = Counter()
    for tokens in document_tokens:
        doc_freq.update(set(tokens))
    _bm25_doc_cache[name] = {
        "hash": content_hash_val,
        "documents": documents,
        "tokens": document_tokens,
        "doc_freq": doc_freq,
        "avgdl": avgdl,
    }
    if re.fullmatch(r"[0-9a-f]{64}", content_hash_val or ""):
        _set_collection_meta_cache(name, content_hash_val, len(documents))


def process_and_store_document(document_url: str, text: str, title: str = "") -> dict:
    current_hash = content_hash(text)
    collection = get_collection(document_url)
    if _stored_content_hash(collection, use_cache=False) == current_hash:
        return {"indexed": False, "reason": "unchanged", "content_hash": current_hash}
    _invalidate_bm25_cache(_get_collection_name(document_url))
    if _collection_count(collection) > 0:
        _delete_collection(_get_collection_name(document_url))
        collection = get_collection(document_url)
    doc_chunks = chunk_document_text(text)
    if not doc_chunks:
        return {"indexed": False, "reason": "empty", "content_hash": current_hash}
        
    chunks = []
    metadatas = []
    indexed_at = int(time.time())
    
    for i, c in enumerate(doc_chunks):
        chunks.append(_source_prefixed_chunk(c["text"], document_url, title))
        metadatas.append({
            "url": document_url, "source_url": document_url, "title": title,
            "source_type": "uploaded_document", "chunk_index": i,
            "content_hash": current_hash, "indexed_at": indexed_at,
            "section": c["heading"],
            "section_normalized": c["normalized_heading"]
        })
        
    ids = [f"doc_chunk_{i}" for i in range(len(chunks))]
    batch_embed_chunks(collection, chunks, metadatas, ids)
    prune_collection_count()
    return {"indexed": True, "reason": "updated", "chunks": len(chunks), "content_hash": current_hash}


def process_and_store_content(url: str, text: str) -> dict:
    current_hash = content_hash(text)
    collection = get_collection(url)
    if _stored_content_hash(collection, use_cache=False) == current_hash:
        return {"indexed": False, "reason": "unchanged", "content_hash": current_hash}
    _invalidate_bm25_cache(_get_collection_name(url))
    if _collection_count(collection) > 0:
        _delete_collection(_get_collection_name(url))
        collection = get_collection(url)
    chunks = [_source_prefixed_chunk(chunk, url) for chunk in chunk_text(text)]
    if not chunks:
        return {"indexed": False, "reason": "empty", "content_hash": current_hash}
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    indexed_at = int(time.time())
    metadatas = [
        {"url": url, "source_url": url, "chunk_index": i,
         "content_hash": current_hash, "indexed_at": indexed_at}
        for i in range(len(chunks))
    ]
    batch_embed_chunks(collection, chunks, metadatas, ids)
    prune_collection_count()
    return {"indexed": True, "reason": "updated", "chunks": len(chunks), "content_hash": current_hash}


def process_and_store_pages(collection_url: str, pages: list[dict]) -> dict:
    fingerprint_source = "\n".join(
        f"{page.get('url', '')}\n{page.get('title', '')}\n{page.get('content', '')}"
        for page in pages
    )
    current_hash = content_hash(fingerprint_source)
    collection = get_collection(collection_url)
    if _stored_content_hash(collection, use_cache=False) == current_hash:
        return {"indexed": False, "reason": "unchanged", "pages": len(pages), "content_hash": current_hash}
    _invalidate_bm25_cache(_get_collection_name(collection_url))
    if _collection_count(collection) > 0:
        _delete_collection(_get_collection_name(collection_url))
        collection = get_collection(collection_url)
    indexed_at = int(time.time())
    chunks, metadatas, ids = [], [], []
    for page_index, page in enumerate(pages):
        page_url = page.get("url", collection_url)
        title = page.get("title", "")
        for chunk_index, chunk in enumerate(chunk_text(page.get("content", ""))):
            chunks.append(_source_prefixed_chunk(chunk, page_url, title))
            metadatas.append({
                "url": collection_url, "source_url": page_url, "title": title,
                "page_index": page_index, "chunk_index": chunk_index,
                "content_hash": current_hash, "indexed_at": indexed_at,
            })
            ids.append(f"page_{page_index}_chunk_{chunk_index}")
    if not chunks:
        return {"indexed": False, "reason": "empty", "pages": len(pages), "content_hash": current_hash}
    batch_embed_chunks(collection, chunks, metadatas, ids)
    prune_collection_count()
    return {"indexed": True, "reason": "updated", "pages": len(pages), "chunks": len(chunks), "content_hash": current_hash}


def is_content_current(url: str, text_hash: str) -> bool:
    collection = get_collection(url)
    return _stored_content_hash(collection) == text_hash


def _keyword_score(question: str, document: str) -> float:
    terms = {term for term in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(term) > 2}
    if not terms:
        return 0.0
    document_terms = set(re.findall(r"[a-zA-Z0-9]+", document.lower()))
    return len(terms & document_terms) / len(terms)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2]


def is_link_question(question: str) -> bool:
    terms = set(re.findall(r"[a-zA-Z0-9]+", question.lower()))
    return bool(terms & LINK_QUESTION_TERMS)


def retrieve_link_context(collection, question: str, max_chunks: int = 4, content_hash_val: str = "") -> list[str]:
    col_hash = content_hash_val or _stored_content_hash(collection)
    cached_docs = _get_cached_documents(collection, col_hash)
    if cached_docs is not None:
        documents = cached_docs
    else:
        try:
            result = collection.get(include=["documents"])
        except Exception as exc:
            if _is_missing_collection_error(exc):
                return []
            if _repair_collection_after_error(collection, exc):
                return []
            raise
        documents = [d for d in (result.get("documents") or []) if isinstance(d, str) and d.strip()]
        _set_cached_documents(collection, col_hash, documents)
    link_chunks = [d for d in documents if "Page links:" in d]
    if not link_chunks:
        return []
    return sorted(link_chunks, key=lambda d: _keyword_score(question, d), reverse=True)[:max_chunks]


def retrieve_bm25_candidates(collection, question: str, max_chunks: int = HYBRID_BM25_CANDIDATES, content_hash_val: str = "") -> list[tuple[float, str]]:
    """Rank all chunks with BM25. Uses in-memory cache — no repeated collection.get() calls."""
    col_hash = content_hash_val or _stored_content_hash(collection)
    name = _collection_name(collection)
    cached = _bm25_doc_cache.get(name)

    if cached and cached.get("hash") == col_hash:
        documents = cached["documents"]
        document_tokens = cached["tokens"]
        doc_freq = cached["doc_freq"]
        avgdl = cached["avgdl"]
    else:
        cached_docs = _get_cached_documents(collection, col_hash)
        if cached_docs is not None:
            documents = cached_docs
        else:
            try:
                result = collection.get(include=["documents"])
            except Exception as exc:
                if _is_missing_collection_error(exc):
                    return []
                if _repair_collection_after_error(collection, exc):
                    return []
                raise
            documents = [d for d in (result.get("documents") or []) if isinstance(d, str) and d.strip()]
        _set_cached_documents(collection, col_hash, documents)
        cached = _bm25_doc_cache.get(name, {})
        document_tokens = cached.get("tokens", [_tokenize(d) for d in documents])
        doc_freq = cached.get("doc_freq", Counter())
        avgdl = cached.get("avgdl", 0.0)

    query_terms = _tokenize(question)
    if not documents or not query_terms:
        return []

    k1, b = 1.5, 0.75
    ranked = []
    for document, tokens in zip(documents, document_tokens):
        if not tokens:
            continue
        term_counts = Counter(tokens)
        score = 0.0
        for term in query_terms:
            tf = term_counts.get(term, 0)
            if not tf:
                continue
            df = doc_freq.get(term, 0)
            idf = math.log(1 + ((len(documents) - df + 0.5) / (df + 0.5)))
            denominator = tf + k1 * (1 - b + b * (len(tokens) / max(avgdl, 1)))
            score += idf * ((tf * (k1 + 1)) / denominator)
        if score > 0:
            ranked.append((score, document))
    return sorted(ranked, reverse=True)[:max_chunks]


def semantic_query_text(question: str) -> str:
    if "bge-" in EMBEDDING_MODEL_NAME.lower():
        return f"Represent this sentence for searching relevant passages: {question}"
    return question


def rrf_merge_candidates(
    vector_items: list[tuple[float, str]],
    bm25_items: list[tuple[float, str]],
    priority_chunks: list[str],
    rrf_k: int = 60,
) -> list[tuple[float, str]]:
    rrf_scores: dict[str, float] = {}
    for rank, (_, document) in enumerate(vector_items, start=1):
        rrf_scores[document] = rrf_scores.get(document, 0.0) + 1.0 / (rrf_k + rank)
    for rank, (_, document) in enumerate(bm25_items, start=1):
        rrf_scores[document] = rrf_scores.get(document, 0.0) + 1.0 / (rrf_k + rank)
    for document in set(priority_chunks):
        if document not in rrf_scores:
            rrf_scores[document] = 0.0
        rrf_scores[document] += 1.0 / (rrf_k + 1)
    return sorted(
        ((score, document) for document, score in rrf_scores.items()),
        key=lambda x: x[0],
        reverse=True,
    )


def rerank_candidates(question: str, candidates: list[tuple[float, str]]) -> tuple[list[tuple[float, str]], bool]:
    if not candidates:
        return [], False
    reranker = get_reranker_model()
    if reranker is None:
        return candidates, False
    rerank_set = candidates[:HYBRID_RERANK_CANDIDATES]
    passthrough = candidates[HYBRID_RERANK_CANDIDATES:]
    pairs = [[question, document] for _, document in rerank_set]
    try:
        scores = reranker.predict(pairs)
        reranked = sorted(
            [(float(score), document) for score, (_, document) in zip(scores, rerank_set)],
            reverse=True
        )
        return [*reranked, *passthrough], True
    except Exception as exc:
        print(f"Reranking failed, using RRF score only: {exc}")
        return candidates, False


def retrieval_cache_key(url: str, marker: str, question: str, n_results: int, candidate_count: int) -> str:
    normalized_question = " ".join(question.lower().split())
    return f"{url}|{marker}|{normalized_question}|n:{n_results}|c:{candidate_count}|rerank:{ENABLE_RERANKER}"


def get_cached_retrieval(key: str) -> Optional[dict]:
    cached = retrieval_cache.get(key)
    if cached is None:
        return None
    retrieval_cache.move_to_end(key)
    return cached.copy()


def store_cached_retrieval(key: str, value: dict) -> None:
    retrieval_cache[key] = value.copy()
    retrieval_cache.move_to_end(key)
    while len(retrieval_cache) > RETRIEVAL_CACHE_MAX_ITEMS:
        retrieval_cache.popitem(last=False)


def compress_context(chunks: list[str], question: str, max_chars: int = NORMAL_CONTEXT_MAX_CHARS) -> str:
    """Compress chunks to fit within max_chars. Default is tighter for normal chat speed."""
    compressed = []
    used = 0
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunk = chunk[:remaining].rsplit(" ", 1)[0].strip()
        compressed.append(chunk)
        used += len(chunk)
    return "\n\n...\n\n".join(compressed)


def _target_sections_for_question(question: str) -> set[str]:
    tokens = set(_tokenize(question))
    targets = set()
    for section, terms in SECTION_QUERY_TERMS.items():
        if tokens & terms:
            targets.add(_normalize_heading(section))
    return targets


def _document_metadata_map(collection) -> dict[str, dict]:
    try:
        result = collection.get(include=["documents", "metadatas"])
    except Exception as exc:
        if _is_missing_collection_error(exc):
            return {}
        if _repair_collection_after_error(collection, exc):
            return {}
        raise
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    return {
        document: metadata or {}
        for document, metadata in zip(documents, metadatas)
        if isinstance(document, str)
    }


def _section_match_score(metadata: dict, target_sections: set[str]) -> float:
    if not target_sections:
        return 0.0
    section = _normalize_heading(str(metadata.get("section_normalized") or metadata.get("section") or ""))
    if section in target_sections:
        return 0.035
    if section == "qualifications" and target_sections & {"education", "requirements"}:
        return 0.02
    if section == "summary" and target_sections & {"skills", "experience"}:
        return 0.01
    return 0.0


def _apply_section_boost(
    candidates: list[tuple[float, str]],
    metadata_by_document: dict[str, dict],
    target_sections: set[str],
) -> list[tuple[float, str]]:
    if not target_sections:
        return candidates
    boosted = [
        (score + _section_match_score(metadata_by_document.get(document, {}), target_sections), document)
        for score, document in candidates
    ]
    return sorted(boosted, reverse=True)


def extract_sources(chunks: list[str], metadata_by_document: dict[str, dict] | None = None, max_sources: int = 4) -> list[dict]:
    sources = []
    seen = set()
    metadata_by_document = metadata_by_document or {}
    for index, chunk in enumerate(chunks):
        source_match = re.search(r"^Source:\s*(.+)$", chunk, re.MULTILINE)
        if not source_match:
            continue
        source_url = source_match.group(1).strip()
        metadata = metadata_by_document.get(chunk, {})
        section = str(metadata.get("section") or "").strip()
        section_normalized = str(metadata.get("section_normalized") or "").strip()
        source_key = (source_url, section_normalized or section)
        if source_key in seen:
            continue
        title_match = re.search(r"^Title:\s*(.+)$", chunk, re.MULTILINE)
        source_type = metadata.get("source_type", "")
        
        # calculate relevance score: start high and decay slightly based on rank order index
        relevance_score = round(max(0.70, 0.98 - (index * 0.05)), 2)
        
        # get last updated timestamp/string
        indexed_at = metadata.get("indexed_at")
        if indexed_at:
            import datetime
            last_updated = datetime.datetime.fromtimestamp(indexed_at).strftime("%B %Y")
        else:
            last_updated = "June 2026"
            
        # extract clean snippet
        snippet = chunk
        for pattern in [r"^Source:\s*.+$", r"^Title:\s*.+$"]:
            snippet = re.sub(pattern, "", snippet, flags=re.MULTILINE)
        snippet = " ".join(snippet.split())[:180] + "..."

        source = {
            "id": f"S{len(sources) + 1}",
            "url": source_url,
            "title": str(metadata.get("title") or (title_match.group(1).strip() if title_match else source_url)),
            "last_updated": last_updated,
            "relevance_score": relevance_score,
            "source_type": "document" if source_type == "uploaded_document" else "page",
            "section": section or "General",
            "snippet": snippet
        }
        sources.append(source)
        seen.add(source_key)
        if len(sources) >= max_sources:
            break
    return sources


def label_context_sources(context: str, sources: list[dict]) -> str:
    labeled = context
    for source in sources:
        source_url = source.get("url", "")
        source_id = source.get("id", "")
        if source_url and source_id:
            labeled = labeled.replace(f"Source: {source_url}", f"Source {source_id}: {source_url}")
    return labeled


def delete_old_collections(max_age_days: int = 14) -> dict:
    cutoff = int(time.time()) - (max_age_days * 24 * 60 * 60)
    deleted = []
    skipped = []
    for collection_info in chroma_client.list_collections():
        name = getattr(collection_info, "name", collection_info)
        if not name.startswith("url_"):
            skipped.append(name)
            continue
        collection = chroma_client.get_collection(name=name, embedding_function=get_embedding_function())
        if _collection_count(collection) == 0:
            _delete_collection(name)
            deleted.append(name)
            continue
        try:
            result = collection.get(limit=1, include=["metadatas"])
        except Exception as exc:
            if _is_missing_collection_error(exc):
                deleted.append(name)
                continue
            if _repair_collection_after_error(collection, exc):
                deleted.append(name)
                continue
            raise
        metadatas = result.get("metadatas") or []
        indexed_at = metadatas[0].get("indexed_at", 0) if metadatas else 0
        if indexed_at and indexed_at < cutoff:
            _delete_collection(name)
            deleted.append(name)
        else:
            skipped.append(name)
    return {"deleted": deleted, "skipped": len(skipped), "max_age_days": max_age_days}


def retrieve_context(url: str, question: str, n_results: int = 5, candidate_count: int = HYBRID_VECTOR_CANDIDATES) -> str:
    result = retrieve_context_with_sources(url, question, n_results, candidate_count)
    return result["context"]


def retrieve_context_with_sources(
    url: str,
    question: str,
    n_results: int = 5,
    candidate_count: int = HYBRID_VECTOR_CANDIDATES,
    context_max_chars: int = NORMAL_CONTEXT_MAX_CHARS,
) -> dict:
    """Retrieve the most relevant chunks. context_max_chars controls compression tightness."""
    collection = get_collection(url)
    collection_count = _collection_count(collection)
    if collection_count == 0:
        return {"context": "", "sources": [], "confidence": "low", "context_chars": 0, "selected_chunks": 0}

    stored_hash = _stored_content_hash(collection)
    cache_marker = stored_hash or str(collection_count)
    cache_key = retrieval_cache_key(url, cache_marker, question, n_results, candidate_count)
    cached = get_cached_retrieval(cache_key)
    if cached:
        cached["cached_retrieval"] = True
        return cached

    bm25_cache_hash = stored_hash or cache_marker
    priority_chunks = retrieve_link_context(collection, question, content_hash_val=bm25_cache_hash) if is_link_question(question) else []
    bm25_candidates = retrieve_bm25_candidates(collection, question, content_hash_val=bm25_cache_hash)
    target_sections = _target_sections_for_question(question)
    metadata_by_document = _document_metadata_map(collection) if target_sections or url.startswith("document://") else {}
    bm25_candidates = _apply_section_boost(bm25_candidates, metadata_by_document, target_sections)

    try:
        results = collection.query(
            query_texts=[semantic_query_text(question)],
            n_results=min(candidate_count, collection_count),
            include=["documents", "distances", "metadatas"]
        )
    except Exception as exc:
        if _is_missing_collection_error(exc):
            return {"context": "", "sources": [], "confidence": "low", "context_chars": 0, "selected_chunks": 0}
        if _repair_collection_after_error(collection, exc):
            return {"context": "", "sources": [], "confidence": "low", "context_chars": 0, "selected_chunks": 0}
        raise

    if not results['documents'] or not results['documents'][0]:
        fallback_chunks = [*priority_chunks, *[d for _, d in bm25_candidates[:n_results]]]
        if fallback_chunks:
            selected = list(dict.fromkeys(fallback_chunks))
            sources = extract_sources(selected, metadata_by_document)
            context = label_context_sources(compress_context(selected, question, context_max_chars), sources)
            payload = {
                "context": context, "sources": sources,
                "confidence": "medium" if selected else "low",
                "context_chars": len(context), "selected_chunks": len(selected),
                "top_score": 0.0, "retrieval_mode": "bm25_fallback", "reranked": False,
            }
            store_cached_retrieval(cache_key, payload)
            return payload
        return {"context": "", "sources": [], "confidence": "low", "context_chars": 0, "selected_chunks": 0}

    documents = results["documents"][0]
    distances = (results.get("distances") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    if metadatas:
        metadata_by_document.update({
            document: metadata or {}
            for document, metadata in zip(documents, metadatas)
            if isinstance(document, str)
        })
    vector_candidates = [
        (1 / (1 + max(distances[i] if i < len(distances) else 1.0, 0)), doc)
        for i, doc in enumerate(documents)
    ]

    merged = rrf_merge_candidates(vector_candidates, bm25_candidates, priority_chunks)
    merged = _apply_section_boost(merged, metadata_by_document, target_sections)
    ranked, reranked = rerank_candidates(question, merged)
    selected = list(dict.fromkeys(doc for _, doc in sorted(ranked, reverse=True)))[:n_results]

    sources = extract_sources(selected, metadata_by_document)
    context = label_context_sources(compress_context(selected, question, context_max_chars), sources)
    top_score = sorted(ranked, reverse=True)[0][0] if ranked else 0.0
    keyword_hits = max((_keyword_score(question, d) for d in selected), default=0.0)

    confidence = "high"
    if keyword_hits == 0:
        confidence = "low"
    elif not reranked and top_score < 0.010:
        confidence = "low"
    elif not reranked and top_score < 0.016:
        confidence = "medium"

    payload = {
        "context": context, "sources": sources, "confidence": confidence,
        "context_chars": len(context), "selected_chunks": len(selected),
        "top_score": round(top_score, 4),
        "retrieval_mode": "rrf_bm25_vector_rerank" if reranked else "rrf_bm25_vector",
        "reranked": reranked,
        "vector_candidates": len(vector_candidates),
        "bm25_candidates": len(bm25_candidates),
        "section_targets": sorted(target_sections),
    }
    store_cached_retrieval(cache_key, payload)
    return payload
