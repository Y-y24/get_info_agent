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
            "Breaking: Major AI Breakthrough Announced Today — Experts Weigh In",
            "http://a.com/1",
        ),
        make_item(
            "Breaking: Major AI Breakthrough Announced Today – Experts Weigh In",
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
