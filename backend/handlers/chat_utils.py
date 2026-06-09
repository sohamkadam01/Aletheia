import re
from typing import Optional

from rag import is_link_question


def normalize_question(question: str) -> str:
    return " ".join(question.lower().split())


def normalize_document_mode(mode: str) -> str:
    mode = (mode or "website").lower().strip()
    return mode if mode in ("website", "document", "compare") else "website"


def mode_scoped_history(history: Optional[list[dict]], document_mode: str) -> list[dict]:
    if not history:
        return []
    return [
        item for item in history
        if isinstance(item, dict) and item.get("document_mode") == document_mode
    ]


def mode_scoped_conversation_memory(memory: Optional[dict], document_mode: str) -> dict:
    if not isinstance(memory, dict):
        return {}

    scoped = dict(memory)
    scoped["current_document_mode"] = document_mode
    turns = memory.get("turns") or []
    scoped["turns"] = [
        turn for turn in turns
        if isinstance(turn, dict) and turn.get("document_mode") == document_mode
    ]

    if document_mode == "website":
        scoped["current_document"] = None
        scoped["fetched_webpage"] = None
    elif document_mode == "document":
        scoped["current_page"] = None
        scoped["fetched_webpage"] = None

    return scoped


def compare_retrieval_query(question: str) -> str:
    normalized = normalize_question(question)
    generic_terms = ("compare", "comparison", "document", "pdf", "uploaded", "website", "page", "content")
    meaningful_terms = [
        term for term in normalized.split()
        if len(term) > 3 and term not in generic_terms
    ]
    if meaningful_terms:
        return (
            f"{question}\n"
            "Also retrieve the main relevant details needed for comparison: features, pricing, dates, "
            "requirements, policies, terms, contact details, limitations, claims, and important differences."
        )
    return (
        "main topics, key claims, features, pricing, dates, requirements, policies, terms, contact details, "
        "limitations, benefits, risks, and important details for comparing two sources"
    )


def conversation_memory_summary(memory: Optional[dict], max_turns: int = 6) -> str:
    if not memory:
        return ""

    parts = []
    current_page = memory.get("current_page") or {}
    current_document = memory.get("current_document") or {}
    fetched_webpage = memory.get("fetched_webpage") or {}

    if current_page.get("url"):
        parts.append(
            f"Current page: {current_page.get('title') or current_page.get('url')} ({current_page.get('url')})"
        )
    if current_document.get("document_id"):
        parts.append(
            f"Current uploaded document: {current_document.get('filename') or 'uploaded document'} "
            f"(id: {current_document.get('document_id')})"
        )
    if fetched_webpage.get("url"):
        parts.append(f"Fetched webpage for comparison: {fetched_webpage.get('url')}")

    turns = memory.get("turns") or []
    if isinstance(turns, list) and turns:
        parts.append("Recent remembered turns:")
        for index, turn in enumerate(turns[-max_turns:], start=1):
            if not isinstance(turn, dict):
                continue
            question = str(turn.get("question") or "").strip()
            answer = str(turn.get("answer") or "").strip()
            mode = str(turn.get("document_mode") or "").strip()
            document = turn.get("document") or {}
            compared_webpage = turn.get("compared_webpage") or {}
            sources = turn.get("sources") or []
            source_urls = [
                str(source.get("url") or "").strip()
                for source in sources
                if isinstance(source, dict) and source.get("url")
            ][:3]

            line = f"{index}. "
            if question:
                line += f"User asked: {question[:220]}. "
            if mode:
                line += f"Mode: {mode}. "
            if document.get("document_id"):
                line += f"Document: {document.get('filename') or document.get('document_id')}. "
            if compared_webpage.get("url"):
                line += f"Compared webpage: {compared_webpage.get('url')}. "
            if source_urls:
                line += f"Sources used: {', '.join(source_urls)}. "
            if answer:
                line += f"Assistant answered: {answer[:360]}"
            parts.append(line.strip())

    return "\n".join(part for part in parts if part).strip()


def memory_augmented_history(history: Optional[list[dict]], memory: Optional[dict]) -> list[dict]:
    items = list(history or [])
    summary = conversation_memory_summary(memory)
    if summary:
        items.append({
            "sender": "assistant",
            "text": f"Conversation memory:\n{summary}"
        })
    return items


def direct_page_context(question: str, text: str, url: str, max_chars: int = 2600) -> str:
    if not question or not text:
        return ""

    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "page", "site",
        "website", "content", "there", "what", "where", "when", "which", "about",
        "tell", "show", "find", "does", "have", "has", "are", "you", "can",
    }
    query_terms = [
        term for term in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if len(term) > 2 and term not in stopwords
    ]
    if not query_terms:
        return ""

    blocks = [
        block.strip()
        for block in re.split(r"\n{2,}|(?<=\.)\s+(?=[A-Z0-9])", text)
        if len(block.strip()) >= 25
    ] or [text.strip()]

    ranked = []
    for block in blocks:
        lower_block = block.lower()
        score = sum(1 for term in query_terms if term in lower_block)
        if score:
            ranked.append((score, min(len(block), 500), block))

    selected = []
    used = 0
    seen = set()
    for _, _, block in sorted(ranked, reverse=True):
        cleaned = " ".join(block.split())
        key = cleaned.lower()
        if key in seen:
            continue
        if used + len(cleaned) > max_chars:
            cleaned = cleaned[:max(0, max_chars - used)].rsplit(" ", 1)[0].strip()
        if not cleaned:
            break
        seen.add(key)
        selected.append(cleaned)
        used += len(cleaned)
        if used >= max_chars:
            break

    if not selected:
        return ""
    snippets = "\n\n...\n\n".join(selected)
    return f"Source: {url}\nDirect matches from the current page:\n{snippets}"


def live_page_context(question: str, text: str, url: str, max_chars: int = 9000) -> str:
    if not text or len(text.strip()) < 20:
        return ""

    direct_context = direct_page_context(question, text, url, max_chars=min(3600, max_chars))
    remaining_chars = max_chars - len(direct_context)
    if remaining_chars < 1600 and direct_context:
        return direct_context[:max_chars]

    lines = []
    seen = set()
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if len(line) < 2:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)

    if not lines:
        return direct_context

    important_prefixes = (
        "indexed url:", "page title:", "title:", "description:", "open graph",
        "table ", "media:", "page links:", "link ",
    )
    overview = []
    body = []
    for line in lines:
        lower_line = line.lower()
        if lower_line.startswith(important_prefixes) or len(line) <= 110:
            overview.append(line)
        else:
            body.append(line)

    chosen = []
    used = len(direct_context)
    for line in [*overview[:120], *body]:
        if used + len(line) + 1 > max_chars:
            break
        chosen.append(line)
        used += len(line) + 1

    page_overview = "\n".join(chosen).strip()
    if direct_context and page_overview:
        return f"{direct_context}\n\nSource: {url}\nVisible live page content:\n{page_overview}"
    if page_overview:
        return f"Source: {url}\nVisible live page content:\n{page_overview}"
    return direct_context


def is_general_knowledge_question(question: str) -> bool:
    normalized = normalize_question(question)
    return normalized.startswith((
        "what is ", "what are ", "who is ", "who are ", "define ", "explain ",
        "meaning of ", "how does ", "how do ", "why does ", "why do ",
    ))


def empty_retrieval(reason: str = "") -> dict:
    payload = {
        "context": "",
        "sources": [],
        "confidence": "low",
        "context_chars": 0,
        "selected_chunks": 0,
        "retrieval_mode": "none",
    }
    if reason:
        payload["fallback_reason"] = reason
    return payload


def _context_terms(text: str) -> set[str]:
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "page", "site", "website",
        "what", "where", "when", "which", "about", "tell", "show", "find", "does", "have",
        "has", "are", "you", "can", "document", "compare", "content", "current", "uploaded",
    }
    return {
        term
        for term in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(term) > 2 and term not in stopwords
    }


def _is_broad_page_request(question: str) -> bool:
    normalized = normalize_question(question)
    return any(
        phrase in normalized
        for phrase in (
            "summarize",
            "summary",
            "key takeaway",
            "key point",
            "main point",
            "overview",
            "explain simply",
            "what is this page about",
            "what is this document about",
        )
    )


def validate_answer_context(retrieval: dict, question: str, mode: str = "website", allow_empty: bool = False) -> dict:
    context = retrieval.get("context", "") or ""
    sources = retrieval.get("sources", []) or []
    source_keys = set()
    deduped_sources = []
    issues = []

    for source in sources:
        key = (source.get("url") or source.get("title") or source.get("id") or "").strip().lower()
        if not key or key in source_keys:
            continue
        source_keys.add(key)
        deduped_sources.append(source)
    retrieval["sources"] = deduped_sources

    if not context.strip():
        issues.append("empty_context")
    if len(context.strip()) < 80 and not allow_empty:
        issues.append("thin_context")
    if mode in ("website", "compare") and not deduped_sources and context.strip():
        issues.append("missing_sources")

    query_terms = _context_terms(question)
    context_terms = _context_terms(context[:12000])
    relevance = 0.0
    if query_terms:
        relevance = len(query_terms & context_terms) / len(query_terms)
        if relevance < 0.10 and not allow_empty and not _is_broad_page_request(question):
            issues.append("low_question_overlap")

    duplicate_ratio = 0.0
    blocks = [
        " ".join(block.split()).lower()
        for block in re.split(r"\n{2,}|(?:\.\s+)", context)
        if len(block.strip()) > 80
    ]
    if blocks:
        duplicate_ratio = 1 - (len(set(blocks)) / len(blocks))
        if duplicate_ratio > 0.35:
            issues.append("duplicate_context")

    confidence = retrieval.get("confidence", "low")
    if issues and confidence == "high":
        retrieval["confidence"] = "medium"
    if any(issue in issues for issue in ("empty_context", "thin_context", "low_question_overlap")):
        retrieval["confidence"] = "low"

    passed = not any(issue in issues for issue in ("empty_context", "thin_context")) or allow_empty
    return {
        "passed": passed,
        "issues": issues,
        "source_count": len(deduped_sources),
        "context_chars": len(context),
        "question_overlap": round(relevance, 3),
        "duplicate_ratio": round(duplicate_ratio, 3),
        "confidence_after_validation": retrieval.get("confidence", confidence),
    }


def fast_follow_up_suggestions(question: str, scope: str = "page") -> list[str]:
    normalized = normalize_question(question)

    if is_link_question(question):
        return ["Summarize relevant options", "Explain next steps", "List page actions"]

    if any(term in normalized for term in ["summary", "summarize", "main point", "key takeaway"]):
        return ["List key details", "Explain simply", "What matters most?"]

    if scope == "site":
        return ["Find related topics", "Summarize results", "Explain next steps"]

    return ["Tell me more", "Summarize this page", "Explain simply"]
