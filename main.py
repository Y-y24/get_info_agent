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
