from __future__ import annotations


def _live_page_retrieval(url: str, live_context: str) -> dict:
    return {
        "context": (
            "Primary live webpage context captured from the currently open page:\n"
            f"{live_context}"
        ),
        "sources": [{"id": "S1", "url": url, "title": url, "source_type": "website"}],
        "confidence": "high" if len(live_context) >= 200 else "medium",
        "context_chars": len(live_context),
        "selected_chunks": 1,
        "retrieval_mode": "live_page_primary",
        "reranked": False,
    }


def _merge_indexed_retrieval(primary: dict, indexed: dict) -> dict:
    indexed_context = indexed.get("context", "")
    if not indexed_context:
        return primary

    primary["context"] += (
        "\n\nSupplemental indexed matches from local cache:\n"
        f"{indexed_context}"
    )
    primary["context_chars"] = len(primary["context"])
    primary["selected_chunks"] += indexed.get("selected_chunks", 0)
    primary["retrieval_mode"] = f"live_page_primary+{indexed.get('retrieval_mode', 'indexed')}"

    for source in indexed.get("sources", []):
        source.setdefault("source_type", "website")
        if not any(existing.get("url") == source.get("url") for existing in primary["sources"]):
            primary["sources"].append(source)

    return primary


def retrieve_website_context(
    *,
    document_mode: str,
    url: str,
    question: str,
    retrieval_question: str,
    latest_page_text: str,
    n_results: int,
    empty_retrieval,
    live_page_context,
    retrieve_context,
    is_link_question,
    live_retrieval_question: str = "",
    context_max_chars: int = 2400,
) -> dict:
    retrieval = empty_retrieval()
    primary_live_context = ""

    if document_mode in ("website", "compare") and latest_page_text:
        primary_live_context = live_page_context(
            live_retrieval_question or retrieval_question,
            latest_page_text,
            url,
            max_chars=context_max_chars,
        )
        if primary_live_context:
            retrieval = _live_page_retrieval(url, primary_live_context)

    should_fetch_indexed = (
        not primary_live_context
        or (document_mode in ("website", "compare") and is_link_question(question))
    )
    if document_mode in ("website", "compare") and should_fetch_indexed:
        indexed_retrieval = retrieve_context(
            url,
            retrieval_question,
            n_results=n_results,
            context_max_chars=context_max_chars,
        )
        if primary_live_context:
            retrieval = _merge_indexed_retrieval(retrieval, indexed_retrieval)
        else:
            retrieval = indexed_retrieval

    return retrieval


def retrieve_document_context(
    *,
    document_mode: str,
    document_url: str,
    retrieval_question: str,
    n_results: int,
    empty_retrieval,
    retrieve_context,
    full_document_retrieval: bool = False,
    context_max_chars: int = 3200,
) -> dict:
    document_retrieval = empty_retrieval()
    if document_mode not in ("document", "compare"):
        return document_retrieval

    document_retrieval = retrieve_context(
        document_url,
        retrieval_question,
        n_results=n_results,
        context_max_chars=context_max_chars,
    )
    for index, source in enumerate(document_retrieval.get("sources", []), start=1):
        original_id = source.get("id", f"S{index}")
        document_retrieval["context"] = document_retrieval.get("context", "").replace(
            f"Source {original_id}:",
            f"Document D{index}:",
        )
        source["id"] = f"D{index}"
        source["source_type"] = "document"

    return document_retrieval


def label_website_sources_for_mode(retrieval: dict, document_mode: str) -> dict:
    for index, source in enumerate(retrieval.get("sources", []), start=1):
        source["id"] = source.get("id", f"S{index}")
        source["source_type"] = "website"
    return retrieval


def retrieve_page_and_document_contexts(
    *,
    document_mode: str,
    url: str,
    document_url: str,
    question: str,
    retrieval_question: str,
    latest_page_text: str,
    n_results: int,
    full_document_retrieval: bool = False,
    empty_retrieval,
    live_page_context,
    retrieve_context,
    is_link_question,
    live_retrieval_question: str = "",
    context_max_chars: int = 2400,
    document_context_max_chars: int = 3200,
) -> tuple[dict, dict]:
    retrieval = retrieve_website_context(
        document_mode=document_mode,
        url=url,
        question=question,
        retrieval_question=retrieval_question,
        live_retrieval_question=live_retrieval_question,
        latest_page_text=latest_page_text,
        n_results=n_results,
        empty_retrieval=empty_retrieval,
        live_page_context=live_page_context,
        retrieve_context=retrieve_context,
        is_link_question=is_link_question,
        context_max_chars=context_max_chars,
    )
    document_retrieval = retrieve_document_context(
        document_mode=document_mode,
        document_url=document_url,
        retrieval_question=retrieval_question,
        n_results=n_results,
        full_document_retrieval=full_document_retrieval,
        empty_retrieval=empty_retrieval,
        retrieve_context=retrieve_context,
        context_max_chars=document_context_max_chars,
    )

    if document_mode == "document":
        retrieval = label_website_sources_for_mode(retrieval, document_mode)

    return retrieval, document_retrieval
