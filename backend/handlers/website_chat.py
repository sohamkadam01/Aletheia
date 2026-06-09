from __future__ import annotations


def should_search_external(
    *,
    context: str,
    retrieval_question: str,
    retrieval_confidence: str,
    is_general_knowledge_question,
    needs_external_search=None,  # kept for signature compat but no longer called
) -> bool:
    """Decide whether to fall back to external search.

    Previously this called needs_external_search() which made a full LLM round-trip
    just to decide whether to search. Now we use the RAG confidence score directly —
    it's already computed and costs nothing extra.
    """
    weak_general_question = (
        is_general_knowledge_question(retrieval_question)
        and retrieval_confidence in ("low", "medium")
    )
    # Only trigger external search when context is empty or confidence is low
    # on a general knowledge question. Never call an LLM just to check.
    return not context or (weak_general_question and retrieval_confidence == "low")


def should_escalate_for_weak_context(
    *,
    context_validation: dict,
    retrieval_confidence: str,
) -> bool:
    issues = set((context_validation or {}).get("issues") or [])
    return (
        retrieval_confidence == "low"
        or "empty_context" in issues
        or "thin_context" in issues
        or "low_question_overlap" in issues
    )


def external_permission_response(
    *,
    answer_time_ms: int,
    retrieval_time_ms: int,
    context: str,
    retrieval: dict,
    retrieval_question: str,
    retrieval_confidence: str,
) -> dict:
    return {
        "answer": "I could not find enough information on the current page. I can search DuckDuckGo if you approve.",
        "requires_external_permission": True,
        "confidence": retrieval_confidence,
        "sources": retrieval.get("sources", []),
        "suggestions": ["Use DuckDuckGo", "Ask about this page", "Summarize this page"],
        "used_external_search": False,
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "context_chars": retrieval.get("context_chars", len(context)),
            "selected_chunks": retrieval.get("selected_chunks", 0),
            "confidence": retrieval_confidence,
            "retrieval_mode": retrieval.get("retrieval_mode", ""),
            "reranked": retrieval.get("reranked", False),
            "retrieval_question": retrieval_question,
            "external_permission_required": True,
        },
    }


def empty_website_response(
    *,
    answer_time_ms: int,
    retrieval_time_ms: int,
    requires_index: bool,
) -> dict:
    return {
        "answer": "I couldn't find relevant information on this page or from external search.",
        "requires_index": requires_index,
        "confidence": "low",
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "provider": "none",
            "model": "",
            "context_chars": 0,
            "retrieval_time_ms": retrieval_time_ms,
            "fallback_reason": "No relevant context retrieved.",
        },
    }
