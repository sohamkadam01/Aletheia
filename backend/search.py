import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


SEARCH_TIMEOUT_SECONDS = 8
USER_AGENT = "WebsiteChatbot/1.0 (+local assistant)"
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
HIGH_QUALITY_SUFFIXES = (".gov", ".edu")
HIGH_QUALITY_DOMAINS = {
    "docs.python.org",
    "developer.mozilla.org",
    "learn.microsoft.com",
    "support.google.com",
    "wikipedia.org",
}


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


def _is_low_quality_result(result: dict) -> bool:
    href = result.get("href", "")
    domain = _domain(href)
    if not href.startswith(("http://", "https://")):
        return True
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in LOW_QUALITY_DOMAINS):
        return True
    if re.search(r"/(tag|author|category|login|signup|search)(/|$)", urlparse(href).path.lower()):
        return True
    return False


def _quality_score(result: dict, query_terms: set[str]) -> float:
    title = result.get("title", "") or ""
    body = result.get("body", "") or ""
    href = result.get("href", "") or ""
    domain = _domain(href)
    searchable = f"{title} {body} {domain}".lower()

    score = 0.0
    if query_terms:
        score += sum(1 for term in query_terms if term in searchable) / len(query_terms)
    if any(domain.endswith(suffix) for suffix in HIGH_QUALITY_SUFFIXES):
        score += 0.45
    if any(domain == trusted or domain.endswith(f".{trusted}") for trusted in HIGH_QUALITY_DOMAINS):
        score += 0.35
    if any(word in domain for word in ("docs", "developer", "support", "official")):
        score += 0.2
    if len(body) >= 80:
        score += 0.1
    return score


def _clean_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "iframe", "svg", "canvas", "nav", "footer"]):
        element.decompose()

    root = soup.select_one("article") or soup.select_one("main") or soup.select_one('[role="main"]') or soup.body or soup
    lines = []
    seen = set()
    for raw_line in root.get_text("\n", strip=True).splitlines():
        line = " ".join(raw_line.split())
        if len(line) < 35:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return "\n".join(lines)


def _extract_page_content(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            return ""
        text = _clean_html_text(response.text)
        return text[:MAX_EXTRACT_CHARS].rsplit(" ", 1)[0].strip()
    except Exception as exc:
        print(f"External result extraction failed for {url}: {exc}")
        return ""


def _filtered_results(query: str, max_results: int) -> list[dict]:
    query_terms = _query_terms(query)
    with DDGS() as ddgs:
        raw_results = list(ddgs.text(query, max_results=max(max_results * 3, 10)))

    ranked = []
    seen_domains = set()
    for result in raw_results:
        if _is_low_quality_result(result):
            continue

        domain = _domain(result.get("href", ""))
        if not domain or domain in seen_domains:
            continue

        score = _quality_score(result, query_terms)
        if score < 0.18:
            continue

        seen_domains.add(domain)
        ranked.append((score, result))

    return [
        {**result, "quality_score": round(score, 2), "domain": _domain(result.get("href", ""))}
        for score, result in sorted(ranked, reverse=True)[:max_results]
    ]


def search_duckduckgo(query: str, max_results: int = 5) -> str:
    """
    Search DuckDuckGo, filter low-quality results, fetch readable page content,
    and return source-grounded external context.
    """
    try:
        results = _filtered_results(query, max_results)
        if not results:
            return ""

        formatted_results = [
            "External Search Results (DuckDuckGo, filtered and extracted):"
        ]
        for index, result in enumerate(results, 1):
            title = result.get("title", "No Title")
            snippet = result.get("body", "")
            href = result.get("href", "")
            extracted = _extract_page_content(href)
            content = extracted or snippet
            if not content:
                continue

            formatted_results.append(
                "\n".join([
                    f"{index}. {title}",
                    f"Source: {href}",
                    f"Domain: {result.get('domain', '')}",
                    f"Quality score: {result.get('quality_score', 0)}",
                    f"Extracted content: {content}",
                ])
            )

        return "\n\n".join(formatted_results) if len(formatted_results) > 1 else ""
    except Exception as e:
        print(f"DuckDuckGo search failed: {str(e)}")
        return ""
