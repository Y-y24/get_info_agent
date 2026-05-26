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
