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
