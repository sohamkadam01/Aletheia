"""Workflow discovery helpers for website-mode process questions."""

from __future__ import annotations

import os
import re
import json
from typing import Callable
from urllib.parse import urlparse

import requests

from crawler import crawl_website, is_same_site, site_key
from scraper import clean_text


WORKFLOW_QUESTION_RE = re.compile(
    r"\b("
    r"how\s+(do|can)\s+i\s+(apply|register|enroll|enrol|submit|file|get|start|join)|"
    r"how\s+to\s+(apply|register|enroll|enrol|submit|file|get|start|join)|"
    r"what\s+is\s+the\s+(process|procedure|workflow|steps?|application\s+process)|"
    r"(application|admission|onboarding|visa|tender|registration|enrollment|enrolment)\s+"
    r"(process|procedure|workflow|steps?)|"
    r"(step\s+by\s+step|end\s+to\s+end|from\s+start\s+to\s+finish)"
    r")\b",
    re.IGNORECASE,
)

DOCUMENT_EXTENSIONS = (".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".html", ".htm")
DOCUMENT_LABEL_RE = re.compile(
    r"\b(form|notice|circular|brochure|prospectus|guideline|instruction|admission|apply|"
    r"application|fee|eligibility|document|required|tender|visa|onboarding)\b",
    re.IGNORECASE,
)
ACTION_RE = re.compile(
    r"\b(apply|register|submit|upload|download|fill|attach|pay|visit|verify|login|sign\s+in|"
    r"create|send|email|print|book|schedule|collect|complete|choose|select|check)\b",
    re.IGNORECASE,
)


def is_workflow_question(question: str) -> bool:
    return bool(WORKFLOW_QUESTION_RE.search(question or ""))


def _filename_from_url(url: str) -> str:
    path = urlparse(url).path
    filename = os.path.basename(path) or "linked-document.txt"
    return filename[:120]


def _is_likely_document_link(link: dict, root_url: str) -> bool:
    url = link.get("url") or ""
    label = link.get("label") or ""
    parsed_path = urlparse(url).path.lower()
    return (
        is_same_site(url, root_url)
        and (
            parsed_path.endswith(DOCUMENT_EXTENSIONS)
            or DOCUMENT_LABEL_RE.search(label)
            or DOCUMENT_LABEL_RE.search(parsed_path.replace("-", " "))
        )
    )


def _score_workflow_page(page: dict, question: str) -> int:
    text = f"{page.get('title', '')}\n{page.get('content', '')}".lower()
    score = 0
    question_terms = {term for term in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(term) > 3}
    score += sum(2 for term in question_terms if term in text)
    score += len(ACTION_RE.findall(text[:12000]))
    score += len(re.findall(r"\b(eligibility|deadline|fee|documents?|form|apply|registration|admission|submit)\b", text))
    return score


def _download_document_text(
    url: str,
    filename: str,
    extract_document_text: Callable[[str, bytes], str],
    max_bytes: int = 8 * 1024 * 1024,
) -> str:
    response = requests.get(url, headers={"User-Agent": "WebsiteChatbot/1.0"}, timeout=15)
    response.raise_for_status()
    data = response.content[: max_bytes + 1]
    if len(data) > max_bytes:
        raise ValueError("Document is too large for workflow discovery.")
    return clean_text(extract_document_text(filename, data))


def discover_workflow_sources(
    start_url: str,
    question: str,
    extract_document_text: Callable[[str, bytes], str],
    max_pages: int = 18,
    max_documents: int = 8,
) -> dict:
    crawl_result = crawl_website(start_url, max_pages=max_pages)
    root = crawl_result.get("site_url") or site_key(start_url)
    pages = crawl_result.get("pages", [])
    errors = list(crawl_result.get("errors", []))

    ranked_pages = sorted(pages, key=lambda page: _score_workflow_page(page, question), reverse=True)
    document_links = []
    seen_urls = set()
    for page in ranked_pages:
        for link in page.get("links", []):
            url = link.get("url") or ""
            if not url or url in seen_urls or not _is_likely_document_link(link, root):
                continue
            seen_urls.add(url)
            document_links.append({**link, "source_page": page.get("url", "")})
            if len(document_links) >= max_documents:
                break
        if len(document_links) >= max_documents:
            break

    document_pages = []
    for index, link in enumerate(document_links, start=1):
        url = link.get("url", "")
        filename = _filename_from_url(url)
        try:
            text = _download_document_text(url, filename, extract_document_text)
            if len(text.strip()) < 40:
                continue
            title = link.get("label") or filename
            document_pages.append({
                "url": url,
                "title": title,
                "content": "\n".join([
                    f"Downloaded document: {title}",
                    f"Document URL: {url}",
                    f"Linked from: {link.get('source_page', '')}",
                    "",
                    text[:100000],
                ]),
                "links": [],
                "source_type": "linked_document",
                "document_index": index,
            })
        except Exception as exc:
            errors.append({"url": url, "error": f"document_fetch_failed: {exc}"})

    combined_pages = pages + document_pages
    return {
        "site_url": root,
        "start_url": start_url,
        "pages": combined_pages,
        "html_pages": len(pages),
        "documents": len(document_pages),
        "document_links": document_links,
        "errors": errors,
    }


def parse_json_safely(text: str) -> dict | None:
    """Safely extract and parse a JSON object from text."""
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Match JSON block
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # Find the first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1].strip())
        except Exception:
            pass

    return None


def topological_sort(steps: list[dict]) -> list[dict]:
    """Perform topological sort on steps based on depends_on field."""
    if not steps:
        return []

    # Map IDs and Titles to steps for easy dependency resolution
    id_to_step = {}
    title_to_step = {}
    for step in steps:
        s_id = str(step.get("id") or "").strip().lower()
        s_title = str(step.get("title") or "").strip().lower()
        if s_id:
            id_to_step[s_id] = step
        if s_title:
            title_to_step[s_title] = step

    def find_step_id(ref: str) -> str | None:
        ref_clean = str(ref).strip().lower()
        if ref_clean in id_to_step:
            return str(id_to_step[ref_clean].get("id") or "")
        if ref_clean in title_to_step:
            return str(title_to_step[ref_clean].get("id") or "")
        # Substring search in titles
        for title, step in title_to_step.items():
            if ref_clean in title or title in ref_clean:
                return str(step.get("id") or "")
        return None

    # Adjacency list and in-degrees
    adj = {str(step.get("id") or idx): [] for idx, step in enumerate(steps)}
    in_degree = {str(step.get("id") or idx): 0 for idx, step in enumerate(steps)}

    for idx, step in enumerate(steps):
        s_id = str(step.get("id") or idx)
        deps = step.get("depends_on") or []
        if isinstance(deps, str):
            deps = [deps]
        for dep in deps:
            dep_id = find_step_id(dep)
            if dep_id and dep_id != s_id:
                adj[dep_id].append(s_id)
                in_degree[s_id] += 1

    # Order priority preservation using Kahn's algorithm
    id_to_index = {str(step.get("id") or idx): idx for idx, step in enumerate(steps)}
    queue = [str(step.get("id") or idx) for idx, step in enumerate(steps) if in_degree[str(step.get("id") or idx)] == 0]
    queue.sort(key=lambda x: id_to_index[x])

    sorted_ids = []
    while queue:
        queue.sort(key=lambda x: id_to_index[x])
        curr = queue.pop(0)
        sorted_ids.append(curr)
        for neighbor in adj.get(curr, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_ids) != len(steps):
        # Fallback to original order if cycle or orphan detected
        return steps

    step_map = {str(step.get("id") or idx): step for idx, step in enumerate(steps)}
    return [step_map[s_id] for s_id in sorted_ids]


def format_workflow_as_markdown(workflow_data: dict, confidence: str) -> str:
    """Format structured workflow data into V2 markdown format."""
    metadata = workflow_data.get("metadata") or {}
    steps = workflow_data.get("steps") or []

    req_docs = metadata.get("required_documents_count") or metadata.get("required_documents") or 0
    if req_docs == 0:
        req_docs = sum(1 for s in steps if s.get("requirement"))

    lines = [
        "### Workflow",
        "",
        "Workflow Summary",
        f"Steps: {len(steps)}",
        f"Required Documents: {req_docs}",
        f"Confidence: {confidence.capitalize()}",
        ""
    ]

    id_to_title = {s.get("id"): s.get("title") for s in steps if s.get("id")}

    for idx, step in enumerate(steps, start=1):
        lines.append(f"{idx}. {step.get('title')}")
        
        if step.get("summary"):
            lines.append(f"   - Detail: {step.get('summary')}")

        if step.get("requirement"):
            lines.append(f"   - Requirement: {step.get('requirement')}")

        deps = step.get("depends_on") or []
        if isinstance(deps, str):
            deps = [deps]
        if deps:
            dep_titles = [id_to_title.get(d, d) for d in deps if d]
            if dep_titles:
                lines.append(f"   - Dependency: {', '.join(dep_titles)}")

        if step.get("fee"):
            lines.append(f"   - Fee: {step.get('fee')}")

        if step.get("deadline"):
            lines.append(f"   - Deadline: {step.get('deadline')}")

        if step.get("branch"):
            lines.append(f"   - Branch: {step.get('branch')}")

        if step.get("source"):
            lines.append(f"   - Source: {step.get('source')}")

        lines.append("")

    return "\n".join(lines)


def check_cancelled(cancel_event):
    if cancel_event and cancel_event.is_set():
        from fastapi import HTTPException
        raise HTTPException(status_code=499, detail="Request cancelled.")


def discover_workflow(
    question: str,
    context: str,
    generate_fn: Callable,
    ollama_model: str | None = None,
    openrouter_model: str | None = None,
    gemini_model: str | None = None,
    force_provider: str = "",
    confidence: str = "medium",
    cancel_event = None,
) -> dict:
    """Run tiered workflow discovery: fast single-pass extraction, with agentic loop fallback."""
    check_cancelled(cancel_event)

    # Stage 1: Fast Single-Pass Extraction
    fast_instructions = (
        "You are the Workflow Extraction Engine. Extract the complete step-by-step application or process workflow from the context.\n"
        "You MUST respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        "  \"confidence\": \"high\" | \"low\",\n"
        "  \"metadata\": {\n"
        "     \"estimated_time\": \"Estimated duration (e.g. 20 mins) or 'Unknown'\",\n"
        "     \"required_documents_count\": integer (number of required forms/documents),\n"
        "     \"fee_details\": \"Fee details (e.g. ₹500) or 'None'\"\n"
        "  },\n"
        "  \"steps\": [\n"
        "     {\n"
        "        \"id\": \"unique_id\",\n"
        "        \"title\": \"Step title\",\n"
        "        \"summary\": \"One-sentence action description\",\n"
        "        \"depends_on\": [\"dependency_id_1\", ...],\n"
        "        \"requirement\": \"Required documents or empty string\",\n"
        "        \"deadline\": \"Deadline date/info or empty string\",\n"
        "        \"fee\": \"Fee details or empty string\",\n"
        "        \"branch\": \"Conditional routing or empty string\",\n"
        "        \"source\": \"Source URL or document name\"\n"
        "     }\n"
        "  ]\n"
        "}\n"
        "Do NOT output markdown code blocks unless they contain this JSON. Output ONLY the JSON."
    )

    llm_result = generate_fn(
        context=context,
        question=question,
        history=None,
        ollama_model=ollama_model,
        openrouter_model=openrouter_model,
        gemini_model=gemini_model,
        force_provider=force_provider,
        confidence=confidence,
        feedback_guidance=fast_instructions,
        concise_answer=False,
        document_mode="website",
        cancel_event=cancel_event,
    )
    
    check_cancelled(cancel_event)
    raw_answer = llm_result.get("answer") or ""
    parsed_wf = parse_json_safely(raw_answer)

    # Determine confidence
    wf_confidence = "low"
    if parsed_wf and isinstance(parsed_wf, dict):
        wf_confidence = str(parsed_wf.get("confidence") or "low").lower()

    if wf_confidence == "high" and parsed_wf and parsed_wf.get("steps"):
        sorted_steps = topological_sort(parsed_wf["steps"])
        parsed_wf["steps"] = sorted_steps
        markdown_answer = format_workflow_as_markdown(parsed_wf, "high")
        return {
            "ok": True,
            "answer": markdown_answer,
            "provider": llm_result.get("provider", ""),
            "model": llm_result.get("model", ""),
            "confidence": "high",
        }

    # Stage 2: Fallback Agentic Reconstruction
    check_cancelled(cancel_event)
    
    # Pass 1: Action Extraction
    pass1_instructions = (
        "Pass 1: Extract all action sentences and concrete tasks relevant to the question.\n"
        "You MUST respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        "  \"actions\": [\n"
        "     {\n"
        "        \"title\": \"Action name\",\n"
        "        \"summary\": \"Short action summary\",\n"
        "        \"source\": \"Source URL or document name\"\n"
        "     }\n"
        "  ]\n"
        "}"
    )
    p1_result = generate_fn(
        context=context,
        question=question,
        history=None,
        ollama_model=ollama_model,
        openrouter_model=openrouter_model,
        gemini_model=gemini_model,
        force_provider=force_provider,
        confidence=confidence,
        feedback_guidance=pass1_instructions,
        concise_answer=False,
        document_mode="website",
        cancel_event=cancel_event,
    )
    
    check_cancelled(cancel_event)
    p1_raw = p1_result.get("answer") or ""
    parsed_p1 = parse_json_safely(p1_raw)
    actions_str = json.dumps(parsed_p1) if parsed_p1 else p1_raw

    # Pass 2: Dependency & Rule Analysis
    pass2_instructions = (
        "Pass 2: Analyze the provided actions alongside the website context. Identify dependencies, prerequisites, requirements, branching conditions, deadlines, and fees.\n"
        "You MUST respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        "  \"dependencies\": [\n"
        "     {\n"
        "        \"action_title\": \"Action title matching the input\",\n"
        "        \"depends_on\": [\"Prerequisite action title\", ...],\n"
        "        \"requirements\": [\"Required forms/documents\"],\n"
        "        \"deadlines\": [\"Deadline info\"],\n"
        "        \"fees\": [\"Fee info\"],\n"
        "        \"branches\": [\"Conditional branching rules\"]\n"
        "     }\n"
        "  ]\n"
        "}"
    )
    p2_result = generate_fn(
        context=context + f"\n\nActions to analyze:\n{actions_str}",
        question=question + " (Analyze dependencies and rules)",
        history=None,
        ollama_model=ollama_model,
        openrouter_model=openrouter_model,
        gemini_model=gemini_model,
        force_provider=force_provider,
        confidence=confidence,
        feedback_guidance=pass2_instructions,
        concise_answer=False,
        document_mode="website",
        cancel_event=cancel_event,
    )
    
    check_cancelled(cancel_event)
    p2_raw = p2_result.get("answer") or ""
    parsed_p2 = parse_json_safely(p2_raw)
    dependencies_str = json.dumps(parsed_p2) if parsed_p2 else p2_raw

    # Pass 3: Workflow Construction
    pass3_instructions = (
        "Pass 3: Final step reconstruction.\n"
        "Using the actions and dependencies, compile the final ordered list of steps.\n"
        "You MUST respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        "  \"metadata\": {\n"
        "     \"estimated_time\": \"Estimated duration or 'Unknown'\",\n"
        "     \"required_documents_count\": integer,\n"
        "     \"fee_details\": \"Fee details\"\n"
        "  },\n"
        "  \"steps\": [\n"
        "     {\n"
        "        \"id\": \"unique_id\",\n"
        "        \"title\": \"Step title\",\n"
        "        \"summary\": \"Short action description\",\n"
        "        \"depends_on\": [\"prerequisite_step_id\", ...],\n"
        "        \"requirement\": \"Required documents or empty string\",\n"
        "        \"deadline\": \"Deadline info or empty string\",\n"
        "        \"fee\": \"Fee info or empty string\",\n"
        "        \"branch\": \"Branching condition or empty string\",\n"
        "        \"source\": \"Source URL or document name\"\n"
        "     }\n"
        "  ]\n"
        "}"
    )
    
    combined_actions_deps = f"Actions:\n{actions_str}\n\nDependencies & Rules:\n{dependencies_str}"
    p3_result = generate_fn(
        context=context + f"\n\nReconstruction Data:\n{combined_actions_deps}",
        question=question,
        history=None,
        ollama_model=ollama_model,
        openrouter_model=openrouter_model,
        gemini_model=gemini_model,
        force_provider=force_provider,
        confidence=confidence,
        feedback_guidance=pass3_instructions,
        concise_answer=False,
        document_mode="website",
        cancel_event=cancel_event,
    )
    
    check_cancelled(cancel_event)
    p3_raw = p3_result.get("answer") or ""
    parsed_p3 = parse_json_safely(p3_raw)

    if parsed_p3 and parsed_p3.get("steps"):
        sorted_steps = topological_sort(parsed_p3["steps"])
        parsed_p3["steps"] = sorted_steps
        markdown_answer = format_workflow_as_markdown(parsed_p3, "low")
        return {
            "ok": True,
            "answer": markdown_answer,
            "provider": p3_result.get("provider", ""),
            "model": p3_result.get("model", ""),
            "confidence": "low",
        }

    return {
        "ok": True,
        "answer": p3_raw if p3_raw.strip() else "I could not reconstruct a structured workflow.",
        "provider": p3_result.get("provider", ""),
        "model": p3_result.get("model", ""),
        "confidence": "low",
    }


def workflow_followups() -> list[str]:
    return [
        "What documents do I need?",
        "Where do I download the forms?",
        "What are the fees and deadlines?",
    ]
