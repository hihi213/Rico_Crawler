from __future__ import annotations

from typing import Any

from src.core.config import Selectors


class NoticeParser:
    def __init__(self, selectors: Selectors) -> None:
        self._selectors = selectors

    def parse_list(self, page: Any) -> list[Any]:
        raise NotImplementedError("NoticeParser is not implemented yet.")

    def parse_detail(self, page: Any) -> dict[str, Any]:
        raise NotImplementedError("NoticeParser is not implemented yet.")
