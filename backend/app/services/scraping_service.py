"""
Web scraping service — best-effort, never crashes the pipeline.
"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FREE_SOURCES = [
    "https://www.crunchbase.com/lists/notable-saas-companies",  # may work partially
    "https://techcrunch.com/",
    "https://wamda.com/companies",  # MENA startups
]


async def fetch_url(url: str, timeout: float = 8.0) -> str:
    """Fetch a URL and return raw text. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return ""


def extract_companies_from_html(html: str) -> List[Dict[str, str]]:
    """Parse raw HTML and try to extract company name + description pairs."""
    soup = BeautifulSoup(html, "html.parser")
    companies = []

    # Remove nav, header, footer noise
    for tag in soup(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Strategy 1: look for article/card-like elements with headings
    articles = soup.find_all(["article", "section", "div"], class_=re.compile(
        r'(card|company|startup|result|item|listing)', re.I
    ))
    for article in articles[:20]:
        heading = article.find(["h1", "h2", "h3", "h4"])
        if heading:
            name = heading.get_text(strip=True)
            if len(name) < 3 or len(name) > 80:
                continue
            para = article.find("p")
            desc = para.get_text(strip=True) if para else ""
            if name and len(name) > 2:
                companies.append({"company_name": name, "description": desc[:300]})

    # Strategy 2: fallback — grab all headings
    if len(companies) < 3:
        for tag in soup.find_all(["h2", "h3"])[:30]:
            name = tag.get_text(strip=True)
            if 3 <= len(name) <= 80 and not any(
                skip in name.lower() for skip in ["menu", "search", "login", "sign", "nav"]
            ):
                companies.append({"company_name": name, "description": ""})

    return companies[:15]


async def scrape_queries(queries: List[str]) -> List[Dict[str, str]]:
    """
    Try fetching search results from DuckDuckGo HTML for each query.
    Best-effort — returns whatever we can get.
    """
    companies = []
    seen = set()

    for query in queries[:3]:  # limit requests
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        html = await fetch_url(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        results = soup.find_all("div", class_="result__body")
        for result in results[:8]:
            title_el = result.find("a", class_="result__a")
            snippet_el = result.find("a", class_="result__snippet")
            if title_el:
                name = title_el.get_text(strip=True)
                desc = snippet_el.get_text(strip=True) if snippet_el else ""
                # Clean up — skip navigation/generic results
                if (
                    len(name) > 3
                    and name not in seen
                    and not any(s in name.lower() for s in ["page", "home", "index"])
                ):
                    seen.add(name)
                    companies.append({"company_name": name, "description": desc[:300]})

    return companies
