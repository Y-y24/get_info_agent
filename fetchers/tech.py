import logging
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

TOP_N = 30


class HackerNewsFetcher(Fetcher):
    TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
    ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or []

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.TOP_STORIES_URL, timeout=10)
            resp.raise_for_status()
            ids = resp.json()[:TOP_N]
        except Exception as e:
            logger.warning(f"HN top stories fetch failed: {e}")
            return []

        items = []
        for story_id in ids:
            try:
                r = requests.get(
                    self.ITEM_URL.format(story_id), timeout=10
                )
                r.raise_for_status()
                data = r.json()
                title = data.get("title", "")
                url = data.get("url") or (
                    f"https://news.ycombinator.com/item?id={story_id}"
                )
                if title:
                    items.append(Item(
                        title=title,
                        url=url,
                        source="hackernews",
                        snippet=title,
                        category="tech",
                    ))
            except Exception as e:
                logger.debug(f"HN item {story_id} failed: {e}")
                continue

        items = filter_by_keywords(items, self.keywords)
        logger.info(f"HackerNews: fetched {len(items)} items")
        return items


class GitHubTrendingFetcher(Fetcher):
    URL = "https://github.com/trending?since=daily"

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or []

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"GitHub Trending fetch failed: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for article in soup.select("article.Box-row"):
            h2 = article.select_one("h2 a")
            if not h2:
                continue
            href = h2.get("href", "").strip()
            full_name = " ".join(h2.stripped_strings)
            desc_el = article.select_one("p.col-9")
            description = desc_el.get_text(strip=True) if desc_el else ""

            items.append(Item(
                title=full_name,
                url=f"https://github.com{href}",
                source="github_trending",
                snippet=description or full_name,
                category="tech",
            ))

        items = filter_by_keywords(items, self.keywords)
        logger.info(f"GitHub Trending: fetched {len(items)} items")
        return items


class PapersWithCodeFetcher(Fetcher):
    URL = "https://paperswithcode.com/"

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or []

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Papers with Code fetch failed: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for card in soup.select("div.paper-card, div.item"):
            title_el = card.select_one("h1 a, h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            url = (
                f"https://paperswithcode.com{href}"
                if href.startswith("/")
                else href
            )
            abstract_el = card.select_one("p.item-strip-abstract, p.abstract")
            snippet = (
                abstract_el.get_text(strip=True) if abstract_el else title
            )

            items.append(Item(
                title=title,
                url=url,
                source="paperswithcode",
                snippet=snippet,
                category="tech",
            ))

        items = filter_by_keywords(items, self.keywords)
        logger.info(f"Papers with Code: fetched {len(items)} items")
        return items


ALL_TECH_FETCHERS = {
    "hackernews": HackerNewsFetcher,
    "github_trending": GitHubTrendingFetcher,
    "paperswithcode": PapersWithCodeFetcher,
}
