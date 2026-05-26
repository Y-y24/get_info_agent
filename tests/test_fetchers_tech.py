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
    assert items[0].url == "https://github.com/example/project"


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
