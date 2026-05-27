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
        f"Summarized {len(summarized)} items"
    )
    return summarized
