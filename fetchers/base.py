from dataclasses import dataclass, field
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
