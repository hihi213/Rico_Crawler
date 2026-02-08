from __future__ import annotations  # 타입 힌트 전방 참조 허용.

from typing import Any, Optional  # 범용 타입과 선택적 타입.

from src.core.config import CrawlConfig  # 크롤링 설정 모델.
from src.infrastructure.parser import NoticeParser  # 파서 인터페이스.
from src.infrastructure.repository import NoticeRepository  # 저장소 인터페이스.


class CrawlerService:  # 크롤링 비즈니스 로직 계층.
    def __init__(  # 의존성 주입.
        self,
        config: CrawlConfig,  # 크롤링 설정.
        repo: NoticeRepository,  # 저장소 구현체.
        parser: NoticeParser,  # 파서 구현체.
    ) -> None:
        self._config = config  # 설정 보관.
        self._repo = repo  # 저장소 보관.
        self._parser = parser  # 파서 보관.

    def run(self, page: Any, max_pages: Optional[int]) -> None:  # 실행 진입점.
        raise NotImplementedError("CrawlerService is not implemented yet.")  # 미구현.
