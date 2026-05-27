import json
import logging
import requests
from .base import Item, Fetcher

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class WeiboFetcher(Fetcher):
    URL = "https://weibo.com/ajax/side/hotSearch"

    def fetch(self) -> list[Item]:
        headers = {
            **HEADERS,
            "Referer": "https://weibo.com/",
        }
        try:
            resp = requests.get(self.URL, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Weibo fetch failed: {e}")
            return []

        items = []
        for entry in data.get("data", {}).get("realtime", []):
            word = entry.get("word", "")
            if not word:
                continue
            raw_hot = entry.get("raw_hot", 0)
            items.append(Item(
                title=word,
                url=f"https://s.weibo.com/weibo?q={word}",
                source="weibo",
                snippet=f"微博热搜，实时热度: {raw_hot}",
                category="news",
            ))
        logger.info(f"Weibo: fetched {len(items)} items")
        return items[:20]


class ZhihuFetcher(Fetcher):
    URL = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"

    def fetch(self) -> list[Item]:
        headers = {
            **HEADERS,
            "Referer": "https://www.zhihu.com/hot",
        }
        try:
            resp = requests.get(self.URL, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Zhihu fetch failed: {e}")
            return []

        items = []
        for entry in data.get("data", []):
            target = entry.get("target", {})
            title = target.get("title", "")
            qid = target.get("id", "")
            excerpt = target.get("excerpt", "")
            if not title:
                continue
            items.append(Item(
                title=title,
                url=f"https://www.zhihu.com/question/{qid}",
                source="zhihu",
                snippet=excerpt or title,
                category="news",
            ))
        logger.info(f"Zhihu: fetched {len(items)} items")
        return items


class Kr36Fetcher(Fetcher):
    URL = "https://36kr.com/newsflashes"

    def fetch(self) -> list[Item]:
        headers = {
            **HEADERS,
            "Referer": "https://36kr.com/",
        }
        try:
            resp = requests.get(self.URL, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"36kr fetch failed: {e}")
            return []

        items = []
        try:
            prefix = '<script id="__NEXT_DATA__" type="application/json">'
            suffix = "</script>"
            start = resp.text.index(prefix) + len(prefix)
            end = resp.text.index(suffix, start)
            raw = resp.text[start:end]
            data = json.loads(raw)
            newsflashes = (
                data.get("props", {})
                .get("pageProps", {})
                .get("newsflashListData", {})
                .get("data", {})
                .get("newsflashes", [])
            )
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"36kr parse failed: {e}")
            return []

        for nf in newsflashes:
            title = nf.get("title", "")
            desc = nf.get("description", "")
            nid = nf.get("newsflashId", "")
            if not title:
                continue
            items.append(Item(
                title=title,
                url=f"https://36kr.com/newsflashes/{nid}",
                source="36kr",
                snippet=desc or title,
                category="news",
            ))
        logger.info(f"36kr: fetched {len(items)} items")
        return items


class BaiduHotFetcher(Fetcher):
    URL = "https://top.baidu.com/board?tab=realtime"

    def fetch(self) -> list[Item]:
        headers = {
            **HEADERS,
            "Referer": "https://top.baidu.com/",
        }
        try:
            resp = requests.get(self.URL, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Baidu hot fetch failed: {e}")
            return []

        items = []
        try:
            prefix = "<!--s-data:"
            suffix = "-->"
            start = resp.text.index(prefix) + len(prefix)
            end = resp.text.index(suffix, start)
            raw = resp.text[start:end]
            data = json.loads(raw)
            cards = (
                data.get("data", {})
                .get("cards", [{}])[0]
                .get("content", [])
            )
        except (ValueError, KeyError, IndexError, json.JSONDecodeError) as e:
            logger.warning(f"Baidu hot parse failed: {e}")
            return []

        for card in cards:
            title = card.get("word", "")
            desc = card.get("desc", "")
            url = card.get("url", "") or card.get("appUrl", "")
            if not title:
                continue
            items.append(Item(
                title=title,
                url=url or f"https://www.baidu.com/s?wd={title}",
                source="baidu",
                snippet=desc or title,
                category="news",
            ))
        logger.info(f"BaiduHot: fetched {len(items)} items")
        return items[:20]


ALL_NEWS_FETCHERS = {
    "weibo": WeiboFetcher,
    "zhihu": ZhihuFetcher,
    "36kr": Kr36Fetcher,
    "baidu": BaiduHotFetcher,
}
