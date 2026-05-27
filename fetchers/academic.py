import logging
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from .base import Item, Fetcher, filter_by_keywords

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"


class ArxivFetcher(Fetcher):
    def __init__(self, categories: list[str]):
        self.categories = categories

    def _build_url(self) -> str:
        cat_query = "+OR+".join(f"cat:{c}" for c in self.categories)
        params = {
            "search_query": cat_query,
            "start": 0,
            "max_results": 20,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        return f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

    def fetch(self) -> list[Item]:
        url = self._build_url()
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"arXiv fetch failed: {e}")
            return []

        items = []
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            logger.warning(f"arXiv XML parse failed: {e}")
            return []

        ns = {"atom": ATOM_NS}
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            link_el = entry.find("atom:link", ns)

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            summary = (
                summary_el.text.strip()
                if summary_el is not None and summary_el.text
                else ""
            )
            url = (
                link_el.get("href", "").strip()
                if link_el is not None
                else ""
            )
            if not title:
                continue

            items.append(Item(
                title=title,
                url=url,
                source="arxiv",
                snippet=summary[:300] if summary else title,
                category="academic",
            ))
        logger.info(f"arXiv ({','.join(self.categories)}): fetched {len(items)} items")
        return items


class HuggingFaceFetcher(Fetcher):
    URL = "https://huggingface.co/papers"

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or []

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"HuggingFace fetch failed: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for article in soup.select("article"):
            link = article.select_one("a[href*='/papers/']")
            if not link:
                continue
            title = link.get_text(strip=True)
            href = link.get("href", "")
            abstract_el = article.select_one("p")
            snippet = (
                abstract_el.get_text(strip=True) if abstract_el else title
            )

            url = (
                f"https://huggingface.co{href}"
                if href.startswith("/")
                else href
            )
            items.append(Item(
                title=title,
                url=url,
                source="huggingface",
                snippet=snippet[:300],
                category="academic",
            ))
        items = filter_by_keywords(items, self.keywords)
        logger.info(f"HuggingFace: fetched {len(items)} items")
        return items


ALL_ACADEMIC_FETCHERS = {
    "arxiv": ArxivFetcher,
    "huggingface": HuggingFaceFetcher,
}
