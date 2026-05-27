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
        params = (
            f"search_query={urllib.parse.quote(cat_query, safe=':+')}"
            f"&start=0&max_results=20"
            f"&sortBy=submittedDate&sortOrder=descending"
        )
        return f"{ARXIV_API}?{params}"

    def fetch(self) -> list[Item]:
        url = self._build_url()
        resp = None
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                break
            except Exception as e:
                logger.warning(
                    f"arXiv fetch attempt {attempt + 1} failed: {e}"
                )
                if attempt == 2:
                    return []
                import time
                time.sleep(2)

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
    URL = "https://huggingface.co/api/daily_papers"

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or []

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            papers = resp.json()
        except Exception as e:
            logger.warning(f"HuggingFace fetch failed: {e}")
            return []

        items = []
        for paper in papers:
            title = paper.get("title", "")
            paper_id = paper.get("paper", {}).get("id", "")
            summary = paper.get("paper", {}).get("summary", "")
            if not title:
                continue
            url = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""
            items.append(Item(
                title=title,
                url=url,
                source="huggingface",
                snippet=summary[:300] if summary else title,
                category="academic",
            ))
        items = filter_by_keywords(items, self.keywords)
        logger.info(f"HuggingFace: fetched {len(items)} items")
        return items


ALL_ACADEMIC_FETCHERS = {
    "arxiv": ArxivFetcher,
    "huggingface": HuggingFaceFetcher,
}
