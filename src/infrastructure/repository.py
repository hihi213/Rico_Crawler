from __future__ import annotations  # 타입 힌트 전방 참조 허용.

from typing import Any  # 범용 타입.


class NoticeRepository:  # 저장소 인터페이스.
    def __init__(self, sqlite_path: str) -> None:  # DB 경로 주입.
        self._sqlite_path = sqlite_path  # 경로 보관.

    def save_notice(self, notice: Any) -> None:  # 저장 동작.
        raise NotImplementedError("NoticeRepository is not implemented yet.")  # 미구현.
