from __future__ import annotations  # 타입 힌트 전방 참조 허용.

from typing import Any  # 범용 타입.

from src.core.config import Selectors  # 셀렉터 설정 모델.


class NoticeParser:  # 파싱 로직 인터페이스.
    def __init__(self, selectors: Selectors) -> None:  # 셀렉터 주입.
        self._selectors = selectors  # 셀렉터 보관.

    def parse_list(self, page: Any) -> list[Any]:  # 목록 파싱.
        raise NotImplementedError("NoticeParser is not implemented yet.")  # 미구현.

    def parse_detail(self, page: Any) -> dict[str, Any]:  # 상세 파싱.
        raise NotImplementedError("NoticeParser is not implemented yet.")  # 미구현.
