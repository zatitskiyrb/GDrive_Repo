from __future__ import annotations

from abc import ABC, abstractmethod

from models.schemas import Job


class BaseScraper(ABC):
    SOURCE: str = ""

    @abstractmethod
    def search(self, keywords: list[str], location: str, days: int, limit: int = 100) -> list[Job]:
        """Return up to `limit` Job objects matching any of the keywords."""
