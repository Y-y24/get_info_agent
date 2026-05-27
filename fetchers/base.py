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


def filter_by_keywords(items: list[Item], keywords: list[str]) -> list[Item]:
    if not keywords:
        return items
    result = []
    for item in items:
        text = (item.title + " " + item.snippet).lower()
        if any(kw.lower() in text for kw in keywords):
            result.append(item)
    return result
