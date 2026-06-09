from __future__ import annotations

from handlers import compare_chat


MODE_PROFILES = {
    "website": {
        "name": "Website",
        "role": "Answer questions only from the current webpage or indexed website context.",
        "must_not": "Do not use uploaded document context or comparison scoring.",
    },
    "document": {
        "name": "Document",
        "role": "Answer questions only from the uploaded document context.",
        "must_not": "Do not use webpage context, comparison tables, or alignment scores.",
    },
    "compare": {
        "name": "Compare",
        "role": "Compare Document A with Document B and explain matches, gaps, conflicts, and alignment.",
        "must_not": "Do not answer as a single-source website or document summary unless the user explicitly asks for a short setup summary before comparison.",
    },
}


def mode_profile(document_mode: str) -> dict:
    return MODE_PROFILES.get(document_mode, MODE_PROFILES["website"])


def mode_contract(document_mode: str) -> str:
    profile = mode_profile(document_mode)
    return (
        f"ACTIVE MODE: {profile['name']}\n"
        f"Mode job: {profile['role']}\n"
        f"Mode boundary: {profile['must_not']}\n"
    )


def build_mode_context(document_mode: str, website_context: str, document_context: str, question: str = "", provider: str = "") -> str:
    if document_mode == "document":
        if not document_context:
            return ""
        return (
            f"{mode_contract('document')}"
            "MODE: Document. Use only the uploaded document context. Do not use webpage context.\n"
            "Document mode output style: direct answer, document summary, extracted points, risks, or section analysis depending on the question. Never include comparison-only sections.\n"
            "Use only the uploaded document context below. Cite document source labels when useful.\n\n"
            f"Uploaded document context:\n{document_context}"
        )

    if document_mode == "compare":
        alignment_baseline = compare_chat.build_alignment_analysis(document_context, website_context, question, provider)
        return (
            f"{mode_contract('compare')}"
            "MODE: Compare. Use only Document A and Document B for comparison.\n"
            "CURRENT COMPARE PAIR ONLY:\n"
            "- Document A role: uploaded document from the current request.\n"
            "- Document B role: webpage/fetched page from the current request.\n"
            "- Required operation: compare Document A against Document B. Never compare Document A against another document. Never compare Document B against another webpage.\n"
            "Document A is the uploaded document. Document B is the fetched webpage/current website context.\n"
            "Keep source lanes separate: never copy Document A facts into Document B, and never copy Document B facts into Document A.\n"
            "Before scoring, explain the core idea of each source and the basis used for comparison.\n"
            "First infer what the user specifically wants compared, then compare that target across both sources.\n"
            "If the deterministic baseline says INTELLIGENT DOCUMENT COMPARISON FRAMEWORK, follow that document-type-aware strategy and do not use generic semantic similarity scoring.\n"
            "If the deterministic baseline says RESUME VS JOB DESCRIPTION FIT BASELINE, treat the task as candidate-job fit analysis and not document similarity.\n"
            "Use the calculated percentage/score from the deterministic baseline as the final score unless source evidence clearly proves a calculation error; do not invent a new percentage.\n"
            "If the user asks for dates, skills, prices, requirements, policies, features, contacts, or any specific topic, prioritize that target over a generic full-document comparison.\n"
            "Clearly label agreements, differences, missing details, and conflicts.\n\n"
            f"{alignment_baseline}\n"
            "BEGIN SOURCE LANE: DOCUMENT A - UPLOADED DOCUMENT ONLY\n"
            f"{document_context or 'No relevant document context was retrieved.'}\n"
            "END SOURCE LANE: DOCUMENT A\n\n"
            "BEGIN SOURCE LANE: DOCUMENT B - WEBPAGE/FETCHED PAGE ONLY\n"
            f"{website_context or 'No relevant website context was retrieved.'}\n"
            "END SOURCE LANE: DOCUMENT B"
        )

    if not website_context:
        return ""
    return (
        f"{mode_contract('website')}"
        "MODE: Website. Use only the current website/page context. Do not use uploaded document context.\n\n"
        "Website mode output style: answer the user's webpage question directly, with concise explanation, steps, or bullets only when helpful. Never include document-only or comparison-only sections.\n\n"
        f"Website context:\n{website_context}"
    )


def retrieval_confidence_for_mode(
    document_mode: str,
    retrieval: dict,
    document_retrieval: dict,
    website_context: str,
    document_context: str,
) -> str:
    if document_mode == "document":
        return document_retrieval.get("confidence", "low")
    if document_mode == "compare":
        if website_context and document_context:
            return "high"
        if website_context or document_context:
            return "medium"
        return "low"
    return retrieval.get("confidence", "high")


def with_memory_context(memory_summary: str, context: str) -> str:
    if not memory_summary:
        return context
    return (
        f"Conversation memory:\n{memory_summary}\n\n"
        f"Current retrieval context:\n{context or 'No current retrieval context.'}"
    )
