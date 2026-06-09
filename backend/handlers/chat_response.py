from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Cheap token estimate for local observability when providers do not return usage."""
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def estimate_llm_cost_usd(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Best-effort cost estimate. Free/local models intentionally report 0."""
    if not provider or provider.lower() in ("ollama", "none", "cancelled"):
        return 0.0
    if ":free" in (model or "").lower():
        return 0.0
    return 0.0


def combine_sources(*source_lists: list[dict]) -> list[dict]:
    combined = []
    seen = set()

    for sources in source_lists:
        for source in sources or []:
            key = (
                source.get("url")
                or source.get("id")
                or source.get("title")
                or str(source)
            )
            if key in seen:
                continue
            seen.add(key)
            combined.append(source)

    return combined


def suggestions_for_mode(
    document_mode: str,
    question: str,
    url: str,
    fast_suggestions,
) -> list[str]:
    if document_mode == "document":
        return ["Summarize this document", "List key points", "Find risks or gaps"]
    if document_mode == "compare":
        return ["Compare key points", "Show differences", "What is missing?"]
    return fast_suggestions(question, "site" if url.rstrip("/") != url else "page")


def token_cost_metrics(context: str, question: str, answer: str, provider: str, model: str) -> dict:
    input_tokens_estimate = estimate_tokens(context) + estimate_tokens(question)
    output_tokens_estimate = estimate_tokens(answer)
    cost_estimate = estimate_llm_cost_usd(
        provider,
        model,
        input_tokens_estimate,
        output_tokens_estimate,
    )
    return {
        "input_tokens_estimate": input_tokens_estimate,
        "output_tokens_estimate": output_tokens_estimate,
        "llm_cost_usd_estimate": cost_estimate,
    }


def build_chat_response_payload(
    *,
    answer: str,
    combined_sources: list[dict],
    suggestions: list[str],
    used_external_search: bool,
    retrieval_confidence: str,
    llm_result: dict,
    answer_time_ms: int,
    generation_time_ms: int,
    retrieval_time_ms: int,
    retrieval: dict,
    document_retrieval: dict,
    context: str,
    context_validation: dict,
    document_context_validation: dict,
    retrieval_question: str,
    original_question: str,
    concise_answer: bool,
    document_mode: str,
    token_metrics: dict,
) -> dict:
    mode_label = {
        "website": "Website",
        "document": "Document",
        "compare": "Compare",
    }.get(document_mode, "Website")
    return {
        "answer": answer,
        "active_mode": document_mode,
        "active_mode_label": mode_label,
        "sources": combined_sources,
        "suggestions": suggestions,
        "used_external_search": used_external_search,
        "confidence": retrieval_confidence,
        "provider": llm_result["provider"],
        "model": llm_result["model"],
        "fallback_reason": llm_result.get("fallback_reason", ""),
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "generation_time_ms": generation_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "provider": llm_result["provider"],
            "model": llm_result["model"],
            "context_chars": retrieval.get("context_chars", len(context)),
            "document_context_chars": document_retrieval.get("context_chars", 0),
            "selected_chunks": retrieval.get("selected_chunks", 0) + document_retrieval.get("selected_chunks", 0),
            "source_count": len(combined_sources),
            "external_search": used_external_search,
            "confidence": retrieval_confidence,
            "retrieval_mode": retrieval.get("retrieval_mode", ""),
            "reranked": retrieval.get("reranked", False),
            "cached_retrieval": retrieval.get("cached_retrieval", False),
            "context_validation": context_validation,
            "document_context_validation": document_context_validation,
            "fallback_reason": llm_result.get("fallback_reason", ""),
            "retrieval_question": retrieval_question if retrieval_question != original_question else "",
            "concise_answer": concise_answer,
            "document_mode": document_mode,
            "active_mode": document_mode,
            "active_mode_label": mode_label,
            **token_metrics,
        },
    }


def build_chat_observability_payload(
    *,
    request_id: str,
    url: str,
    document_mode: str,
    question: str,
    response_payload: dict,
    retrieval_time_ms: int,
    generation_time_ms: int,
    retrieval: dict,
    retrieval_question: str,
    retrieval_confidence: str,
    used_external_search: bool,
    context_validation: dict,
    document_context_validation: dict,
    token_metrics: dict,
) -> dict:
    metrics = response_payload["metrics"]
    return {
        "request_id": request_id or "",
        "url": url,
        "document_mode": document_mode,
        "question": question[:260],
        "answer_time_ms": metrics["answer_time_ms"],
        "retrieval_time_ms": retrieval_time_ms,
        "generation_time_ms": generation_time_ms,
        "provider": response_payload["provider"],
        "model": response_payload["model"],
        "retrieval_mode": retrieval.get("retrieval_mode", ""),
        "retrieval_question": retrieval_question if retrieval_question != question else "",
        "selected_chunks": metrics["selected_chunks"],
        "source_count": metrics["source_count"],
        "context_chars": metrics["context_chars"],
        "document_context_chars": metrics["document_context_chars"],
        "confidence": retrieval_confidence,
        "used_external_search": used_external_search,
        "cached_retrieval": retrieval.get("cached_retrieval", False),
        "context_validation": context_validation,
        "document_context_validation": document_context_validation,
        "cached_answer": False,
        **token_metrics,
        "fallback_reason": response_payload.get("fallback_reason", ""),
    }


def build_stream_observability_payload(
    *,
    request_id: str,
    url: str,
    document_mode: str,
    question: str,
    answer_time_ms: int,
    retrieval_time_ms: int,
    generation_time_ms: int,
    provider: str,
    model: str,
    retrieval: dict,
    context: str,
    retrieval_question: str,
    retrieval_confidence: str,
    used_external_search: bool,
    context_validation: dict,
    token_metrics: dict,
    fallback_reason: str,
) -> dict:
    return {
        "request_id": request_id or "",
        "url": url,
        "document_mode": document_mode,
        "question": question[:260],
        "answer_time_ms": answer_time_ms,
        "retrieval_time_ms": retrieval_time_ms,
        "generation_time_ms": generation_time_ms,
        "provider": provider,
        "model": model,
        "retrieval_mode": retrieval.get("retrieval_mode", ""),
        "retrieval_question": retrieval_question if retrieval_question != question else "",
        "selected_chunks": retrieval.get("selected_chunks", 0),
        "source_count": len(retrieval.get("sources", [])),
        "context_chars": retrieval.get("context_chars", len(context)),
        "confidence": retrieval_confidence,
        "used_external_search": used_external_search,
        "cached_retrieval": retrieval.get("cached_retrieval", False),
        "context_validation": context_validation,
        **token_metrics,
        "fallback_reason": fallback_reason,
    }


def build_stream_done_event(
    *,
    provider: str,
    model: str,
    retrieval: dict,
    suggestions: list[str],
    used_external_search: bool,
    retrieval_confidence: str,
    fallback_reason: str,
    answer_time_ms: int,
    generation_time_ms: int,
    retrieval_time_ms: int,
    context: str,
    context_validation: dict,
    token_metrics: dict,
) -> dict:
    return {
        "type": "done",
        "provider": provider,
        "model": model,
        "sources": retrieval.get("sources", []),
        "suggestions": suggestions,
        "used_external_search": used_external_search,
        "confidence": retrieval_confidence,
        "fallback_reason": fallback_reason,
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "generation_time_ms": generation_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "provider": provider,
            "model": model,
            "context_chars": retrieval.get("context_chars", len(context)),
            "selected_chunks": retrieval.get("selected_chunks", 0),
            "external_search": used_external_search,
            "confidence": retrieval_confidence,
            "retrieval_mode": retrieval.get("retrieval_mode", ""),
            "cached_retrieval": retrieval.get("cached_retrieval", False),
            "context_validation": context_validation,
            "fallback_reason": fallback_reason,
            "streamed": True,
            **token_metrics,
        },
    }
