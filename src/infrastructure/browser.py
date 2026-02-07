from __future__ import annotations

from typing import Any

from src.core.config import CrawlConfig


class BrowserController:
    def __init__(self, config: CrawlConfig) -> None:
        self._config = config

    def __enter__(self) -> "BrowserController":
        raise NotImplementedError("BrowserController is not implemented yet.")

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def new_page(self) -> Any:
        raise NotImplementedError("BrowserController is not implemented yet.")
