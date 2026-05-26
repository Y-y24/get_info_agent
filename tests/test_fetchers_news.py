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
