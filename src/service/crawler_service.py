from __future__ import annotations

from typing import Any, Optional

from src.core.config import CrawlConfig
from src.infrastructure.parser import NoticeParser
from src.infrastructure.repository import NoticeRepository


class CrawlerService:
    def __init__(
        self,
        config: CrawlConfig,
        repo: NoticeRepository,
        parser: NoticeParser,
    ) -> None:
        self._config = config
        self._repo = repo
        self._parser = parser

    def run(self, page: Any, max_pages: Optional[int]) -> None:
        raise NotImplementedError("CrawlerService is not implemented yet.")
