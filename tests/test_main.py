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

        # Create mock fetcher classes that return controlled items
        MockWeiboFetcher = Mock()
        MockWeiboFetcher.return_value.fetch.return_value = mock_news_items

        MockHNFetcher = Mock()
        MockHNFetcher.return_value.fetch.return_value = []

        MockArxivFetcher = Mock()
        MockArxivFetcher.return_value.fetch.return_value = []

        MockHFFetcher = Mock()
        MockHFFetcher.return_value.fetch.return_value = []

        with patch("main.load_config") as mock_load:
            with patch("main.deduplicate") as mock_dedup:
                with patch("main.summarize_items") as mock_summarize:
                    with patch("main.send_mail") as mock_send:
                        # Patch the fetcher lookup dictionaries in main's namespace
                        with patch.dict("main.ALL_NEWS_FETCHERS",
                                        {"weibo": MockWeiboFetcher}):
                            with patch.dict("main.ALL_TECH_FETCHERS",
                                            {"hackernews": MockHNFetcher}):
                                with patch("main.ArxivFetcher",
                                           MockArxivFetcher):
                                    with patch("main.HuggingFaceFetcher",
                                               MockHFFetcher):
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
