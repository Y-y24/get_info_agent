from dataclasses import dataclass
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


def filter_by_keywords(items: list[Item], keywords: list[str],
                        languages: list[str] | None = None) -> list[Item]:
    if not keywords and not languages:
        return items
    result = []
    for item in items:
        text = (item.title + " " + item.snippet).lower()
        kw_match = not keywords or any(
            kw.lower() in text for kw in keywords
        )
        lang_match = not languages or any(
            lang.lower() in text for lang in languages
        )
        if keywords and languages:
            if kw_match or lang_match:
                result.append(item)
        elif keywords:
            if kw_match:
                result.append(item)
        else:
            if lang_match:
                result.append(item)
    return result
