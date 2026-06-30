import os
import re
from urllib.parse import urlparse

import requests


TAVILY_TIMEOUT_SECONDS = 10
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_API_URL = "https://api.tavily.com/search"
MAX_EXTRACT_CHARS = 1800
LOW_QUALITY_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "pinterest.com",
    "quora.com",
    "reddit.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
    "youtube.com",
}


def has_tavily_key() -> bool:
    return bool(TAVILY_API_KEY)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _query_terms(query: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z0-9]+", query.lower())
        if len(term) > 2
    }


def search_tavily(query: str, max_results: int = 5) -> str:
    """
    Search using Tavily's API — returns AI-optimized, already-extracted content.
    Returns "" on any failure.
    """
    if not TAVILY_API_KEY:
        return ""

    try:
        response = requests.post(
            TAVILY_API_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max(1, min(max_results, 8)),
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=TAVILY_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            print(f"Tavily search failed with {response.status_code}: {response.text[:200]}")
            return ""

        data = response.json()
        results = data.get("results") or []
        if not results:
            return ""

        query_terms = _query_terms(query)
        formatted_results = ["External Search Results (Tavily, filtered):"]
        count = 0
        for result in results[:max_results]:
            href = result.get("url", "")
            domain = _domain(href)
            if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in LOW_QUALITY_DOMAINS):
                continue

            title = result.get("title", "No Title")
            content = (result.get("content") or "").strip()
            if not content:
                continue

            content = content[:MAX_EXTRACT_CHARS].rsplit(" ", 1)[0].strip()
            score = result.get("score", 0)
            count += 1
            formatted_results.append(
                "\n".join([
                    f"{count}. {title}",
                    f"Source: {href}",
                    f"Domain: {domain}",
                    f"Relevance score: {round(float(score), 2) if score else 'n/a'}",
                    f"Extracted content: {content}",
                ])
            )

        return "\n\n".join(formatted_results) if count > 0 else ""
    except Exception as exc:
        print(f"Tavily search failed: {exc}")
        return ""


def tavily_available() -> bool:
    return has_tavily_key()


def search_external(query: str, max_results: int = 5) -> str:
    """
    Unified external search entry point.
    Only uses Tavily.
    Always returns a plain string ready to inject into the LLM context.
    """
    if has_tavily_key():
        result = search_tavily(query, max_results)
        if result:
            return result
        print("Tavily returned no results.")

    return ""
