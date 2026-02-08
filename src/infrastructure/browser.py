from __future__ import annotations  # 타입 힌트 전방 참조 허용.

from typing import Any  # 범용 타입.

from src.core.config import CrawlConfig  # 크롤링 설정 모델.


class BrowserController:  # 브라우저 제어 인터페이스.
    def __init__(self, config: CrawlConfig) -> None:  # 설정 주입.
        self._config = config  # 설정 보관.

    def __enter__(self) -> "BrowserController":  # 컨텍스트 매니저 진입.
        raise NotImplementedError("BrowserController is not implemented yet.")  # 미구현.

    def __exit__(self, exc_type, exc, tb) -> None:  # 컨텍스트 매니저 종료.
        return None  # 예외 전파.

    def new_page(self) -> Any:  # 새 페이지 생성.
        raise NotImplementedError("BrowserController is not implemented yet.")  # 미구현.
