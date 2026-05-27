# 每日资讯摘要推送系统 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Python 自动化管道，每日抓取新闻/科技/学术资讯，经 DeepSeek 摘要后通过 QQ 邮箱推送。

**Architecture:** 模块化 Python 项目，fetchers/ 负责各信息源抓取，summarizer.py 调用 DeepSeek API 生成摘要，mailer.py 组装 HTML 邮件并发送，main.py 编排全流程。GitHub Actions 每天定时触发。

**Tech Stack:** Python 3.12, requests, beautifulsoup4, pyyaml, openai SDK (DeepSeek 兼容接口), smtplib

---

### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `fetchers/__init__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "daily-digest"
version = "0.1.0"
description = "每日资讯摘要推送系统"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32",
    "beautifulsoup4>=4.12",
    "pyyaml>=6.0",
    "openai>=1.0",
    "lxml>=5.0",
]
```

- [ ] **Step 2: 创建 requirements.txt**

```
requests>=2.32
beautifulsoup4>=4.12
pyyaml>=6.0
openai>=1.0
lxml>=5.0
```

- [ ] **Step 3: 创建 config.yaml**

```yaml
academic:
  arxiv_categories: ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "eess.SP"]
  keywords: []

tech:
  sources: ["hackernews", "github_trending", "paperswithcode"]

news:
  sources: ["weibo", "zhihu", "36kr"]

email:
  smtp_host: "smtp.qq.com"
  smtp_port: 587
  from_address: "your@qq.com"
  to_address: "your@qq.com"

deepseek:
  model: "deepseek-chat"
  max_tokens_per_item: 80
```

- [ ] **Step 4: 创建 fetchers/__init__.py（空文件）**

- [ ] **Step 5: 安装依赖并验证**

Run: `pip install -r requirements.txt`
Expected: 所有包安装成功，无错误。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml requirements.txt config.yaml fetchers/__init__.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: 数据模型与配置加载

**Files:**
- Create: `fetchers/base.py`
- Create: `config_loader.py`
- Create: `tests/__init__.py` (空文件)
- Create: `tests/test_config_loader.py`

- [ ] **Step 1: 编写配置加载测试**

```python
# tests/test_config_loader.py
import tempfile
import os
from config_loader import load_config


def test_load_config_parses_yaml():
    yaml_content = """
news:
  sources: ["weibo"]
email:
  to_address: "test@qq.com"
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert config["news"]["sources"] == ["weibo"]
        assert config["email"]["to_address"] == "test@qq.com"
    finally:
        os.unlink(tmp_path)


def test_load_config_defaults():
    yaml_content = "news:\n  sources: []"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert "email" in config
        assert "deepseek" in config
        assert config["email"]["smtp_host"] == "smtp.qq.com"
    finally:
        os.unlink(tmp_path)
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_config_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config_loader'`

- [ ] **Step 3: 编写 fetchers/base.py**

```python
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class Item:
    title: str
    url: str
    source: str
    snippet: str
    category: str  # "news" | "tech" | "academic"


class Fetcher(ABC):
    @abstractmethod
    def fetch(self) -> list[Item]:
        ...
```

- [ ] **Step 4: 编写 config_loader.py**

```python
import os
import yaml


DEFAULTS = {
    "academic": {
        "arxiv_categories": ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "eess.SP"],
        "keywords": [],
    },
    "tech": {
        "sources": ["hackernews", "github_trending", "paperswithcode"],
    },
    "news": {
        "sources": ["weibo", "zhihu", "36kr"],
    },
    "email": {
        "smtp_host": "smtp.qq.com",
        "smtp_port": 587,
        "from_address": "",
        "to_address": "",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "max_tokens_per_item": 80,
    },
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    config = {}
    for section, defaults in DEFAULTS.items():
        section_data = defaults.copy()
        if section in user_config:
            section_data.update(user_config[section])
        config[section] = section_data

    return config
```

- [ ] **Step 5: 运行测试，验证通过**

Run: `python -m pytest tests/test_config_loader.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add fetchers/base.py config_loader.py tests/test_config_loader.py tests/__init__.py
git commit -m "feat: add Item data model and YAML config loader"
```

---

### Task 3: 去重模块

**Files:**
- Create: `dedup.py`
- Create: `tests/test_dedup.py`

- [ ] **Step 1: 编写去重测试**

```python
# tests/test_dedup.py
from fetchers.base import Item
from dedup import deduplicate


def make_item(title, url, source="test", snippet="s", category="news"):
    return Item(title=title, url=url, source=source, snippet=snippet, category=category)


def test_exact_url_dedup():
    items = [
        make_item("A", "http://x.com/1"),
        make_item("B", "http://x.com/1"),
        make_item("C", "http://x.com/2"),
    ]
    result = deduplicate(items)
    assert len(result) == 2
    urls = {r.url for r in result}
    assert urls == {"http://x.com/1", "http://x.com/2"}


def test_similar_title_dedup():
    items = [
        make_item(
            "Deep Learning for Image Recognition",
            "http://a.com/1",
        ),
        make_item(
            "Deep Learning for Image Recognition and Classification",
            "http://b.com/2",
        ),
    ]
    result = deduplicate(items)
    assert len(result) == 1


def test_different_titles_kept():
    items = [
        make_item("Python 3.13 Released", "http://x.com/1"),
        make_item("Rust 1.85 Released", "http://x.com/2"),
    ]
    result = deduplicate(items)
    assert len(result) == 2


def test_keeps_first_occurrence():
    items = [
        make_item("Original Title Here", "http://first.com"),
        make_item("Original Title Here!!!", "http://second.com"),
    ]
    result = deduplicate(items)
    assert result[0].url == "http://first.com"


def test_empty_list():
    assert deduplicate([]) == []
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_dedup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dedup'`

- [ ] **Step 3: 编写 dedup.py**

```python
from difflib import SequenceMatcher


SIMILARITY_THRESHOLD = 0.85


def _normalize(title: str) -> str:
    return title.strip().lower()


def deduplicate(items: list) -> list:
    seen_urls: set[str] = set()
    result: list = []

    for item in items:
        url_key = item.url.strip().rstrip("/")
        if url_key in seen_urls:
            continue

        is_dup = False
        norm_title = _normalize(item.title)
        for kept in result:
            kept_norm = _normalize(kept.title)
            ratio = SequenceMatcher(None, norm_title, kept_norm).ratio()
            if ratio >= SIMILARITY_THRESHOLD:
                is_dup = True
                break

        if not is_dup:
            seen_urls.add(url_key)
            result.append(item)

    return result
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_dedup.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add dedup.py tests/test_dedup.py
git commit -m "feat: add URL and title-similarity deduplication"
```

---

### Task 4: 新闻热点抓取器

**Files:**
- Create: `fetchers/news.py`
- Create: `tests/test_fetchers_news.py`

- [ ] **Step 1: 编写新闻抓取器测试**

```python
# tests/test_fetchers_news.py
from unittest.mock import patch, Mock
from fetchers.news import WeiboFetcher, ZhihuFetcher, Kr36Fetcher
from fetchers.base import Item


def test_weibo_fetcher_parses_hot_search():
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "data": {
            "realtime": [
                {"word": "热搜话题1", "raw_hot": 12345},
                {"word": "热搜话题2", "raw_hot": 9999},
            ]
        }
    }
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp) as mock_get:
        items = WeiboFetcher().fetch()

    assert len(items) == 2
    assert items[0].title == "热搜话题1"
    assert items[0].source == "weibo"
    assert items[0].category == "news"
    assert "s.weibo.com" in items[0].url


def test_weibo_fetcher_empty_data():
    mock_resp = Mock()
    mock_resp.json.return_value = {"data": {"realtime": []}}
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = WeiboFetcher().fetch()

    assert items == []


def test_zhihu_fetcher_parses_hot_list():
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "data": [
            {
                "target": {
                    "title": "知乎热榜问题",
                    "id": 123456,
                    "excerpt": "这是一个热门问题摘要",
                }
            },
            {
                "target": {
                    "title": "另一个热榜问题",
                    "id": 789012,
                    "excerpt": "另一个热门问题摘要",
                }
            },
        ]
    }
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = ZhihuFetcher().fetch()

    assert len(items) == 2
    assert items[0].title == "知乎热榜问题"
    assert items[0].source == "zhihu"
    assert "zhihu.com/question/123456" in items[0].url
    assert items[0].snippet == "这是一个热门问题摘要"


def test_36kr_fetcher_parses_newsflashes():
    html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"newsflashListData":{"data":{
        "newsflashes": [
            {"title": "36氪快讯标题1", "description": "快讯内容1",
             "newsflashId": 111, "createdAt": "2026-05-26T09:00:00Z"},
            {"title": "36氪快讯标题2", "description": "快讯内容2",
             "newsflashId": 222, "createdAt": "2026-05-26T08:00:00Z"}
        ]
    }}}}}
    </script>
    </body></html>
    """
    mock_resp = Mock()
    mock_resp.text = html
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = Kr36Fetcher().fetch()

    assert len(items) == 2
    assert items[0].title == "36氪快讯标题1"
    assert items[0].source == "36kr"
    assert items[0].category == "news"


def test_fetchers_handle_network_error():
    import requests as r

    with patch("requests.get", side_effect=r.RequestException("timeout")):
        items = WeiboFetcher().fetch()
    assert items == []
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_fetchers_news.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetchers.news'`

- [ ] **Step 3: 编写 fetchers/news.py**

```python
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
    )
}


class WeiboFetcher(Fetcher):
    URL = "https://weibo.com/ajax/side/hotSearch"

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=10)
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
        return items


class ZhihuFetcher(Fetcher):
    URL = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"

    def fetch(self) -> list[Item]:
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=10)
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
        try:
            resp = requests.get(self.URL, headers=HEADERS, timeout=10)
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


ALL_NEWS_FETCHERS = {
    "weibo": WeiboFetcher,
    "zhihu": ZhihuFetcher,
    "36kr": Kr36Fetcher,
}
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_fetchers_news.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add fetchers/news.py tests/test_fetchers_news.py
git commit -m "feat: add news fetchers (Weibo, Zhihu, 36kr)"
```

---

### Task 5: 科技前沿抓取器

**Files:**
- Create: `fetchers/tech.py`
- Create: `tests/test_fetchers_tech.py`

- [ ] **Step 1: 编写科技抓取器测试**

```python
# tests/test_fetchers_tech.py
from unittest.mock import patch, Mock
from fetchers.tech import HackerNewsFetcher, GitHubTrendingFetcher


def test_hn_fetcher_fetches_top_stories():
    mock_resp_ids = Mock()
    mock_resp_ids.json.return_value = [40000001, 40000002, 40000003]
    mock_resp_ids.raise_for_status = Mock()

    mock_resp_item = Mock()
    mock_resp_item.json.return_value = {
        "id": 40000001,
        "title": "Show HN: A New Open Source Project",
        "url": "https://github.com/example/project",
    }
    mock_resp_item.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [mock_resp_ids] + [mock_resp_item] * 3
        items = HackerNewsFetcher().fetch()

    assert len(items) == 3
    assert items[0].title == "Show HN: A New Open Source Project"
    assert items[0].source == "hackernews"
    assert items[0].category == "tech"
    assert "news.ycombinator.com" in items[0].url


def test_hn_fetcher_handles_missing_url():
    mock_resp_ids = Mock()
    mock_resp_ids.json.return_value = [40000001]
    mock_resp_ids.raise_for_status = Mock()

    mock_resp_item = Mock()
    mock_resp_item.json.return_value = {
        "id": 40000001,
        "title": "Ask HN: Discussion Topic",
    }
    mock_resp_item.raise_for_status = Mock()

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [mock_resp_ids, mock_resp_item]
        items = HackerNewsFetcher().fetch()

    assert len(items) == 1
    assert "news.ycombinator.com" in items[0].url


def test_github_trending_fetcher_parses_html():
    html = """
    <html><body>
    <article class="Box-row">
      <h2 class="h3 lh-condensed">
        <a href="/owner/repo1" class="Link">
          <span class="text-normal">owner / </span>repo1
        </a>
      </h2>
      <p class="col-9 color-fg-muted my-1 pr-4">A cool open source library</p>
    </article>
    <article class="Box-row">
      <h2 class="h3 lh-condensed">
        <a href="/owner/repo2" class="Link">
          <span class="text-normal">owner / </span>repo2
        </a>
      </h2>
      <p class="col-9 color-fg-muted my-1 pr-4">Another great tool for AI</p>
    </article>
    </body></html>
    """
    mock_resp = Mock()
    mock_resp.text = html
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = GitHubTrendingFetcher().fetch()

    assert len(items) >= 2
    assert all(i.source == "github_trending" for i in items)
    assert all(i.category == "tech" for i in items)
    assert any("repo1" in i.title for i in items)


def test_github_trending_handles_error():
    import requests as r

    with patch("requests.get", side_effect=r.RequestException("timeout")):
        items = GitHubTrendingFetcher().fetch()
    assert items == []
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_fetchers_tech.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetchers.tech'`

- [ ] **Step 3: 编写 fetchers/tech.py**

```python
import logging
import requests
from bs4 import BeautifulSoup
from .base import Item, Fetcher

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

        logger.info(f"HackerNews: fetched {len(items)} items")
        return items


class GitHubTrendingFetcher(Fetcher):
    URL = "https://github.com/trending?since=daily"

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

        logger.info(f"GitHub Trending: fetched {len(items)} items")
        return items


class PapersWithCodeFetcher(Fetcher):
    URL = "https://paperswithcode.com/"

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

        logger.info(f"Papers with Code: fetched {len(items)} items")
        return items


ALL_TECH_FETCHERS = {
    "hackernews": HackerNewsFetcher,
    "github_trending": GitHubTrendingFetcher,
    "paperswithcode": PapersWithCodeFetcher,
}
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_fetchers_tech.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add fetchers/tech.py tests/test_fetchers_tech.py
git commit -m "feat: add tech fetchers (HN, GitHub Trending, Papers with Code)"
```

---

### Task 6: 学术前沿抓取器

**Files:**
- Create: `fetchers/academic.py`
- Create: `tests/test_fetchers_academic.py`

- [ ] **Step 1: 编写学术抓取器测试**

```python
# tests/test_fetchers_academic.py
from unittest.mock import patch, Mock
from fetchers.academic import ArxivFetcher


ARXIV_XML_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Attention Is All You Need</title>
    <id>http://arxiv.org/abs/1706.03762v1</id>
    <summary>We propose a new simple network architecture...</summary>
    <author><name>Ashish Vaswani</name></author>
    <published>2017-06-12T17:57:34Z</published>
    <link href="http://arxiv.org/abs/1706.03762v1" rel="alternate"/>
  </entry>
  <entry>
    <title>BERT: Pre-training of Deep Bidirectional Transformers</title>
    <id>http://arxiv.org/abs/1810.04805v1</id>
    <summary>We introduce a new language representation model...</summary>
    <author><name>Jacob Devlin</name></author>
    <published>2018-10-11T17:57:34Z</published>
    <link href="http://arxiv.org/abs/1810.04805v1" rel="alternate"/>
  </entry>
</feed>"""


def test_arxiv_fetcher_parses_atom_xml():
    mock_resp = Mock()
    mock_resp.text = ARXIV_XML_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = ArxivFetcher(categories=["cs.AI"]).fetch()

    assert len(items) == 2
    assert items[0].title == "Attention Is All You Need"
    assert items[0].source == "arxiv"
    assert items[0].category == "academic"
    assert "arxiv.org/abs/1706.03762" in items[0].url


def test_arxiv_fetcher_builds_correct_query_url():
    fetcher = ArxivFetcher(categories=["cs.AI", "cs.CL"])
    url = fetcher._build_url()
    assert "cat:cs.AI" in url
    assert "cat:cs.CL" in url
    assert "sortBy=submittedDate" in url


def test_huggingface_fetcher_parses_html():
    html = """
    <html><body>
    <article class="flex flex-col">
      <a href="/papers/paper1">Paper Title One</a>
      <p>Abstract text for paper one about machine learning.</p>
    </article>
    <article class="flex flex-col">
      <a href="/papers/paper2">Paper Title Two</a>
      <p>Abstract text for paper two about NLP.</p>
    </article>
    </body></html>
    """
    mock_resp = Mock()
    mock_resp.text = html
    mock_resp.raise_for_status = Mock()

    from fetchers.academic import HuggingFaceFetcher

    with patch("requests.get", return_value=mock_resp):
        items = HuggingFaceFetcher().fetch()

    assert len(items) >= 2
    assert all(i.source == "huggingface" for i in items)
    assert all(i.category == "academic" for i in items)


def test_arxiv_fetcher_empty_response():
    empty_xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
    </feed>"""
    mock_resp = Mock()
    mock_resp.text = empty_xml
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = ArxivFetcher(categories=["cs.AI"]).fetch()

    assert items == []
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_fetchers_academic.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetchers.academic'`

- [ ] **Step 3: 编写 fetchers/academic.py**

```python
import logging
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from .base import Item, Fetcher

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
        logger.info(f"HuggingFace: fetched {len(items)} items")
        return items


ALL_ACADEMIC_FETCHERS = {
    "arxiv": ArxivFetcher,
    "huggingface": HuggingFaceFetcher,
}
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_fetchers_academic.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add fetchers/academic.py tests/test_fetchers_academic.py
git commit -m "feat: add academic fetchers (arXiv, HuggingFace)"
```

---

### Task 7: AI 摘要模块

**Files:**
- Create: `summarizer.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: 编写摘要模块测试**

```python
# tests/test_summarizer.py
from unittest.mock import patch, Mock
from fetchers.base import Item
from summarizer import summarize_items


def make_item(title, snippet="test snippet"):
    return Item(
        title=title,
        url="http://example.com",
        source="test",
        snippet=snippet,
        category="news",
    )


def test_summarize_items_calls_api_and_returns_summaries():
    items = [make_item("Breaking News: Something Happened", "Details...")]

    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="某地发生重大事件，相关方面正在处理中。"))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    result = summarize_items(items, mock_client, model="deepseek-chat", max_tokens=80)

    assert len(result) == 1
    assert result[0].snippet == "某地发生重大事件，相关方面正在处理中。"
    mock_client.chat.completions.create.assert_called_once()


def test_summarize_items_retries_on_failure():
    items = [make_item("Test Title", "Test snippet")]

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = [
        Exception("API error"),
        Exception("API error"),
        Mock(choices=[Mock(message=Mock(content="成功摘要"))]),
    ]

    result = summarize_items(items, mock_client, model="deepseek-chat", max_tokens=80)

    assert len(result) == 1
    assert result[0].snippet == "成功摘要"
    assert mock_client.chat.completions.create.call_count == 3


def test_summarize_items_fallback_on_all_failures():
    items = [make_item("Test Title", "Original snippet text")]

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API down")

    result = summarize_items(items, mock_client, model="deepseek-chat", max_tokens=80)

    assert len(result) == 1
    assert result[0].snippet == "Original snippet text"


def test_summarize_items_empty_list():
    result = summarize_items([], Mock(), model="deepseek-chat", max_tokens=80)
    assert result == []
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_summarizer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'summarizer'`

- [ ] **Step 3: 编写 summarizer.py**

```python
import logging
import time
from fetchers.base import Item

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "用一句中文（30~50字）概括以下内容的要点，直接给出摘要，不要任何前缀：\n"
    "标题：{title}\n"
    "内容：{snippet}"
)

MAX_RETRIES = 2
REQUEST_INTERVAL = 0.5


def summarize_items(
    items: list[Item],
    client,
    model: str = "deepseek-chat",
    max_tokens: int = 80,
) -> list[Item]:
    if not items:
        return []

    summarized = []
    for item in items:
        prompt = PROMPT_TEMPLATE.format(
            title=item.title, snippet=item.snippet
        )

        summary = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                summary = response.choices[0].message.content.strip()
                break
            except Exception as e:
                logger.warning(
                    f"DeepSeek API attempt {attempt + 1} failed "
                    f"for '{item.title[:40]}': {e}"
                )
                if attempt < MAX_RETRIES:
                    time.sleep(1)

        if summary:
            item.snippet = summary
        else:
            logger.info(
                f"Using original snippet as fallback for '{item.title[:40]}'"
            )

        summarized.append(item)
        time.sleep(REQUEST_INTERVAL)

    logger.info(
        f"Summarized {len(summarized)} items, "
        f"{sum(1 for i in summarized if i.snippet != item.snippet)} via API"
    )
    return summarized
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_summarizer.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add summarizer.py tests/test_summarizer.py
git commit -m "feat: add DeepSeek API summarizer with retry and fallback"
```

---

### Task 8: 邮件模块

**Files:**
- Create: `mailer.py`
- Create: `tests/test_mailer.py`

- [ ] **Step 1: 编写邮件模块测试**

```python
# tests/test_mailer.py
import datetime
from unittest.mock import patch, Mock
from fetchers.base import Item
from mailer import build_html, send_mail


def make_item(category, title, snippet, source="test"):
    return Item(
        title=title,
        url="http://example.com",
        source=source,
        snippet=snippet,
        category=category,
    )


def test_build_html_has_correct_structure():
    items = [
        make_item("news", "新闻标题1", "AI摘要内容1"),
        make_item("news", "新闻标题2", "AI摘要内容2"),
        make_item("tech", "科技标题1", "科技摘要1"),
        make_item("academic", "论文标题1", "论文摘要1"),
    ]
    today = datetime.date(2026, 5, 26)

    html = build_html(items, today)

    assert "2026" in html
    assert "5月26日" in html
    assert "新闻热点" in html
    assert "科技前沿" in html
    assert "学术前沿" in html
    assert "新闻标题1" in html
    assert "AI摘要内容1" in html
    assert 'href="http://example.com"' in html


def test_build_html_empty_categories_omitted():
    items = [
        make_item("news", "唯一新闻", "摘要"),
    ]
    today = datetime.date(2026, 5, 26)

    html = build_html(items, today)

    assert "新闻热点" in html
    assert "科技前沿" not in html
    assert "学术前沿" not in html


def test_build_html_empty_items():
    today = datetime.date(2026, 5, 26)
    html = build_html([], today)
    assert "暂无资讯" in html


def test_send_mail_calls_smtp():
    items = [make_item("news", "测试标题", "测试摘要")]
    email_config = {
        "smtp_host": "smtp.qq.com",
        "smtp_port": 587,
        "from_address": "sender@qq.com",
        "to_address": "receiver@qq.com",
    }

    mock_smtp = Mock()
    with patch("smtplib.SMTP", return_value=mock_smtp):
        send_mail(items, email_config, password="test_auth_code")

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("sender@qq.com", "test_auth_code")
    mock_smtp.send_message.assert_called_once()
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_mailer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mailer'`

- [ ] **Step 3: 编写 mailer.py**

```python
import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fetchers.base import Item

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "news": "🔥 新闻热点",
    "tech": "💻 科技前沿",
    "academic": "📚 学术前沿",
}

CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
       'PingFang SC', 'Microsoft YaHei', sans-serif;
       max-width: 720px; margin: 0 auto; padding: 20px;
       background: #f5f5f5; }
.container { background: #fff; border-radius: 8px; padding: 24px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.header { text-align: center; padding-bottom: 16px;
          border-bottom: 1px solid #eee; margin-bottom: 20px; }
.header h1 { color: #1a1a1a; font-size: 22px; margin: 0 0 4px 0; }
.header .date { color: #888; font-size: 14px; }
.section { margin-bottom: 24px; }
.section h2 { color: #333; font-size: 17px; border-left: 3px solid #1677ff;
              padding-left: 10px; margin: 0 0 12px 0; }
.item { padding: 8px 0; border-bottom: 1px dashed #f0f0f0; }
.item:last-child { border-bottom: none; }
.item a { color: #1677ff; text-decoration: none; font-weight: 500; }
.item a:hover { text-decoration: underline; }
.item .summary { color: #555; font-size: 13px; margin-top: 2px; }
.item .source { color: #aaa; font-size: 11px; }
.footer { text-align: center; color: #bbb; font-size: 12px;
          margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; }
"""


def build_html(items: list[Item], date: datetime.date) -> str:
    grouped: dict[str, list[Item]] = {"news": [], "tech": [], "academic": []}
    for item in items:
        if item.category in grouped:
            grouped[item.category].append(item)

    date_str = f"{date.year}年{date.month}月{date.day}日"

    sections_html = ""
    for category, label in CATEGORY_LABELS.items():
        cat_items = grouped.get(category, [])
        if not cat_items:
            continue
        items_html = ""
        for item in cat_items:
            items_html += (
                f'<div class="item">'
                f'<a href="{item.url}">{item.title}</a>'
                f'<span class="source"> [{item.source}]</span>'
                f'<div class="summary">{item.snippet}</div>'
                f'</div>\n'
            )
        count = len(cat_items)
        sections_html += (
            f'<div class="section">'
            f'<h2>{label} ({count}条)</h2>'
            f'{items_html}'
            f'</div>\n'
        )

    if not sections_html:
        sections_html = '<p style="text-align:center;color:#888;">今日暂无资讯</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 每日资讯摘要</h1>
    <div class="date">{date_str}</div>
  </div>
  {sections_html}
  <div class="footer">由 GitHub Actions 自动生成 | {date_str}</div>
</div>
<style>{CSS}</style>
</body>
</html>"""


def send_mail(
    items: list[Item],
    email_config: dict,
    password: str,
) -> None:
    today = datetime.date.today()
    html = build_html(items, today)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"每日资讯摘要 | {today.isoformat()}"
    msg["From"] = email_config["from_address"]
    msg["To"] = email_config["to_address"]
    msg.attach(MIMEText(html, "html", "utf-8"))

    smtp_host = email_config["smtp_host"]
    smtp_port = email_config["smtp_port"]

    logger.info(f"Connecting to {smtp_host}:{smtp_port}")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(email_config["from_address"], password)
        server.send_message(msg)

    logger.info(
        f"Email sent: {len(items)} items to {email_config['to_address']}"
    )
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_mailer.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add mailer.py tests/test_mailer.py
git commit -m "feat: add HTML email builder and QQ SMTP sender"
```

---

### Task 9: 编排入口 main.py

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 编写集成测试**

```python
# tests/test_main.py
import os
import tempfile
from unittest.mock import patch, Mock
from main import main


def test_main_orchestrates_full_pipeline():
    config_yaml = """
news:
  sources: ["weibo"]
tech:
  sources: ["hackernews"]
academic:
  arxiv_categories: ["cs.AI"]
email:
  smtp_host: "smtp.qq.com"
  smtp_port: 587
  from_address: "test@qq.com"
  to_address: "test@qq.com"
deepseek:
  model: "deepseek-chat"
  max_tokens_per_item: 80
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(config_yaml)
        config_path = f.name

    try:
        mock_news_items = [
            type("Item", (), {
                "title": "News", "url": "http://x.com", "source": "weibo",
                "snippet": "s", "category": "news",
            })()
        ]
        mock_summarized = [
            type("Item", (), {
                "title": "News", "url": "http://x.com", "source": "weibo",
                "snippet": "AI摘要", "category": "news",
            })()
        ]

        with patch("main.load_config") as mock_load:
            with patch("fetchers.news.WeiboFetcher") as mock_weibo:
                with patch("fetchers.tech.HackerNewsFetcher") as mock_hn:
                    with patch("fetchers.academic.ArxivFetcher") as mock_arxiv:
                        with patch("main.deduplicate") as mock_dedup:
                            with patch("main.summarize_items") as mock_summarize:
                                with patch("main.send_mail") as mock_send:
                                    with patch("main.OpenAI") as mock_openai:

                                        mock_load.return_value = {
                                            "news": {"sources": ["weibo"]},
                                            "tech": {"sources": ["hackernews"]},
                                            "academic": {"arxiv_categories": ["cs.AI"]},
                                            "email": {
                                                "smtp_host": "smtp.qq.com",
                                                "smtp_port": 587,
                                                "from_address": "test@qq.com",
                                                "to_address": "test@qq.com",
                                            },
                                            "deepseek": {
                                                "model": "deepseek-chat",
                                                "max_tokens_per_item": 80,
                                            },
                                        }
                                        mock_weibo.return_value.fetch.return_value = mock_news_items
                                        mock_hn.return_value.fetch.return_value = []
                                        mock_arxiv.return_value.fetch.return_value = []
                                        mock_dedup.return_value = mock_news_items
                                        mock_summarize.return_value = mock_summarized

                                        with patch.dict(os.environ, {
                                            "DEEPSEEK_API_KEY": "test-key",
                                            "QQ_SMTP_PASSWORD": "test-pass",
                                        }):
                                            main(config_path=config_path)

                                        mock_send.assert_called_once()
    finally:
        os.unlink(config_path)
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: 编写 main.py**

```python
import logging
import os
import sys
from openai import OpenAI
from config_loader import load_config
from dedup import deduplicate
from summarizer import summarize_items
from mailer import send_mail
from fetchers.news import ALL_NEWS_FETCHERS
from fetchers.tech import ALL_TECH_FETCHERS
from fetchers.academic import ArxivFetcher, HuggingFaceFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    deepseek_config = config["deepseek"]
    email_config = config["email"]

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    smtp_password = os.environ.get("QQ_SMTP_PASSWORD", "")

    if not deepseek_key:
        logger.error("DEEPSEEK_API_KEY not set in environment")
        sys.exit(1)
    if not smtp_password:
        logger.error("QQ_SMTP_PASSWORD not set in environment")
        sys.exit(1)

    client = OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com",
    )

    # Fetch news
    all_items = []
    for source_key in config["news"]["sources"]:
        fetcher_cls = ALL_NEWS_FETCHERS.get(source_key)
        if fetcher_cls:
            try:
                items = fetcher_cls().fetch()
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"News fetcher '{source_key}' error: {e}")

    # Fetch tech
    for source_key in config["tech"]["sources"]:
        fetcher_cls = ALL_TECH_FETCHERS.get(source_key)
        if fetcher_cls:
            try:
                items = fetcher_cls().fetch()
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"Tech fetcher '{source_key}' error: {e}")

    # Fetch academic
    arxiv_categories = config["academic"]["arxiv_categories"]
    if arxiv_categories:
        try:
            items = ArxivFetcher(categories=arxiv_categories).fetch()
            all_items.extend(items)
        except Exception as e:
            logger.warning(f"ArXiv fetcher error: {e}")

    try:
        items = HuggingFaceFetcher().fetch()
        all_items.extend(items)
    except Exception as e:
        logger.warning(f"HuggingFace fetcher error: {e}")

    logger.info(f"Total fetched: {len(all_items)} items")

    # Deduplicate
    all_items = deduplicate(all_items)
    logger.info(f"After dedup: {len(all_items)} items")

    # Summarize
    all_items = summarize_items(
        all_items,
        client,
        model=deepseek_config["model"],
        max_tokens=deepseek_config["max_tokens_per_item"],
    )

    # Send email
    send_mail(all_items, email_config, password=smtp_password)
    logger.info("Daily digest sent successfully")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，验证通过**

Run: `python -m pytest tests/test_main.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main orchestration entry point"
```

---

### Task 10: GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: 创建 .github/workflows/daily.yml**

```yaml
name: Daily Digest

on:
  schedule:
    - cron: "0 1 * * *"
  workflow_dispatch:

jobs:
  digest:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run daily digest
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          QQ_SMTP_PASSWORD: ${{ secrets.QQ_SMTP_PASSWORD }}
        run: python main.py

      - name: Upload log on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: digest-logs
          path: ~/.local/state/
          retention-days: 7
```

- [ ] **Step 2: 验证 YAML 语法**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/daily.yml'))"`
Expected: 无输出（加载成功）

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily.yml
git commit -m "ci: add GitHub Actions daily workflow"
```

---

### Task 11: README 与最终验证

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README.md**

```markdown
# Daily Digest — 每日资讯摘要推送

每天自动抓取新闻热点、科技前沿、学术前沿资讯，通过 DeepSeek API 生成中文摘要，邮件推送。

## 信息源

**新闻热点：** 微博热搜、知乎热榜、36氪快讯
**科技前沿：** Hacker News、GitHub Trending、Papers with Code
**学术前沿：** arXiv (cs.AI/CL/CV/LG + eess.SP)、Hugging Face Daily Papers

## 快速开始

1. Fork 此仓库
2. 修改 `config.yaml` 中的邮箱地址
3. 在仓库 Settings → Secrets and variables → Actions 中添加：
   - `DEEPSEEK_API_KEY`：DeepSeek API 密钥 (platform.deepseek.com)
   - `QQ_SMTP_PASSWORD`：QQ邮箱 SMTP 授权码

## 本地运行

```bash
pip install -r requirements.txt
DEEPSEEK_API_KEY=your_key QQ_SMTP_PASSWORD=your_pass python main.py
```

## 定时推送

GitHub Actions 每天北京时间 9:00 自动运行，也可在 Actions 页面手动触发。
```

- [ ] **Step 2: 运行全量单元测试**

Run: `python -m pytest tests/ -v`
Expected: 所有测试 PASS

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

---

## 配置提醒

部署前需要用户完成：
1. 修改 `config.yaml` 中 `email.from_address` 和 `email.to_address` 为实际 QQ 邮箱地址
2. 在 GitHub 仓库 Settings → Secrets 中添加 `DEEPSEEK_API_KEY` 和 `QQ_SMTP_PASSWORD`
3. 手动触发一次 workflow 验证推送正常
