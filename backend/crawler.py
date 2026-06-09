from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


CRAWL_TIMEOUT_SECONDS = 10
USER_AGENT = "WebsiteChatbot/1.0"


def normalize_url(url: str) -> str:
    clean_url, _ = urldefrag(url)
    return clean_url.rstrip("/")


def site_key(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_site(url: str, root_url: str) -> bool:
    parsed_url = urlparse(url)
    parsed_root = urlparse(root_url)
    return parsed_url.scheme in {"http", "https"} and parsed_url.netloc == parsed_root.netloc


def extract_static_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    links = []
    seen = set()

    for element in soup.select("a[href], area[href]"):
        href = (element.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        absolute_url = normalize_url(urljoin(base_url, href))
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https", "mailto", "tel"}:
            continue

        label = " ".join(element.get_text(" ", strip=True).split())
        label = label or element.get("aria-label") or element.get("title") or absolute_url
        key = (label, absolute_url)
        if key in seen:
            continue

        seen.add(key)
        links.append({"label": label, "url": absolute_url, "type": "anchor"})

    return links


def page_text_from_soup(soup: BeautifulSoup) -> str:
    for element in soup(["script", "style", "noscript", "iframe", "svg", "canvas"]):
        element.decompose()

    root = soup.select_one("article") or soup.select_one("main") or soup.select_one('[role="main"]') or soup.body or soup
    text = root.get_text(" ", strip=True)
    return " ".join(text.split())


def format_page_document(url: str, title: str, text: str, links: list[dict]) -> str:
    parts = [f"Page title: {title or url}", f"Page URL: {url}", "", text]

    if links:
        link_lines = []
        for index, link in enumerate(links, start=1):
            link_lines.append(
                f"Link {index}: {link['label']}\nType: {link['type']}\nURL: {link['url']}"
            )
        parts.extend(["", "Page links:", "\n\n".join(link_lines)])

    return "\n".join(part for part in parts if part is not None)


def fetch_page(url: str) -> tuple[str, BeautifulSoup]:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=CRAWL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ValueError(f"Skipping non-HTML content: {content_type}")

    return response.url, BeautifulSoup(response.text, "html.parser")


def crawl_website(start_url: str, max_pages: int = 10) -> dict:
    root = site_key(start_url)
    queue = deque([normalize_url(start_url)])
    visited = set()
    pages = []
    errors = []

    while queue and len(pages) < max_pages:
        current_url = queue.popleft()
        if current_url in visited or not is_same_site(current_url, root):
            continue

        visited.add(current_url)

        try:
            final_url, soup = fetch_page(current_url)
            final_url = normalize_url(final_url)
            title = " ".join((soup.title.string if soup.title and soup.title.string else final_url).split())
            links = extract_static_links(soup, final_url)
            text = page_text_from_soup(soup)
            document = format_page_document(final_url, title, text, links)

            if len(document.strip()) >= 50:
                pages.append({
                    "url": final_url,
                    "title": title,
                    "content": document,
                    "links": links,
                })

            for link in links:
                link_url = normalize_url(link["url"])
                if is_same_site(link_url, root) and link_url not in visited:
                    queue.append(link_url)
        except Exception as exc:
            errors.append({"url": current_url, "error": str(exc)})

    return {
        "site_url": root,
        "start_url": start_url,
        "pages": pages,
        "errors": errors,
    }
