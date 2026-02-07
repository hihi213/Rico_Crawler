from __future__ import annotations

from typing import Any


class NoticeRepository:
    def __init__(self, sqlite_path: str) -> None:
        self._sqlite_path = sqlite_path

    def save_notice(self, notice: Any) -> None:
        raise NotImplementedError("NoticeRepository is not implemented yet.")
