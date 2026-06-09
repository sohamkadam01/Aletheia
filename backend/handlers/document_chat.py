from __future__ import annotations


def missing_document_response() -> dict:
    return {
        "answer": "Please upload a document first, then choose Document or Compare mode.",
        "requires_document": True,
    }


def empty_document_response(
    *,
    answer_time_ms: int,
    retrieval_time_ms: int,
    document_retrieval: dict,
    document_mode: str,
) -> dict:
    return {
        "answer": "I couldn't find relevant information in the uploaded document for that question.",
        "confidence": "low",
        "sources": document_retrieval.get("sources", []),
        "suggestions": ["Summarize this document", "List key points", "Ask about a section"],
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "context_chars": 0,
            "selected_chunks": 0,
            "confidence": "low",
            "document_mode": document_mode,
        },
    }
