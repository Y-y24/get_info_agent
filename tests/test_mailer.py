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
    mock_smtp.__enter__ = Mock(return_value=mock_smtp)
    mock_smtp.__exit__ = Mock(return_value=None)
    with patch("smtplib.SMTP", return_value=mock_smtp):
        send_mail(items, email_config, password="test_auth_code")

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("sender@qq.com", "test_auth_code")
    mock_smtp.send_message.assert_called_once()
