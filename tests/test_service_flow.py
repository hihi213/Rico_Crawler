from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.config import CrawlConfig, Selectors
from src.service.crawler_service import CrawlerService


@dataclass
class StubRepository:
    saved_items: list[Any] = field(default_factory=list)

    def save_list_items(self, items: list[Any]) -> None:
        self.saved_items.extend(items)


@dataclass
class StubParser:
    rows: list[dict[str, Any]]

    def parse_list(self, page: Any) -> list[dict[str, Any]]:
        return self.rows


class StubLocator:
    def __init__(self, exists: bool) -> None:
        self._exists = exists

    def count(self) -> int:
        return 1 if self._exists else 0

    @property
    def first(self) -> "StubLocator":
        return self

    def click(self) -> None:
        return None


class StubPage:
    def goto(self, url: str, wait_until: str | None = None) -> None:
        return None

    def wait_for_selector(self, selector: str) -> None:
        return None

    def wait_for_load_state(self, state: str) -> None:
        return None

    def locator(self, selector: str) -> StubLocator:
        return StubLocator(exists=False)


def test_crawler_service_min_flow() -> None:
    config = CrawlConfig(
        base_url="https://example.com",
        list_url="https://example.com/list",
        max_pages=1,
        timeout_ms=5000,
        retry_count=1,
        retry_backoff_sec=0.1,
        user_agent="test-agent",
        selectors=Selectors(
            list_row="#list tr",
            list_link="#list a",
            pagination_next=None,
        ),
    )
    raw_row = {
        "bidPbancNo": "R26BK01292424",
        "bidPbancOrd": "001",
        "bidPbancNm": "테스트 공고",
        "bidPbancNum": "R26BK01292424-001",
        "pbancSttsCd": "01",
        "pbancSttsCdNm": "등록공고",
        "prcmBsneSeCd": "A",
        "prcmBsneSeCdNm": "용역",
        "bidMthdCd": "B",
        "bidMthdCdNm": "일반경쟁",
        "stdCtrtMthdCd": "C",
        "stdCtrtMthdCdNm": "일반",
        "scsbdMthdCd": "D",
        "scsbdMthdCdNm": "적격심사",
        "pbancPstgDt": "2026/02/06 19:11",
        "pbancKndCd": "E",
        "pbancKndCdNm": "신규",
        "grpNm": "테스트기관",
        "slprRcptDdlnDt": "2026/02/07 10:00",
        "pbancSttsGridCdNm": "입찰개시",
        "rowNum": "1",
        "totCnt": "1",
        "currentPage": "1",
        "recordCountPerPage": "10",
        "nextRowYn": "N",
    }
    repo = StubRepository()
    parser = StubParser(rows=[raw_row])
    service = CrawlerService(config, repo, parser)

    service.run(StubPage(), max_pages=1)

    assert len(repo.saved_items) == 1
