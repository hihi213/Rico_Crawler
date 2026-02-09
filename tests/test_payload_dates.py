from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

import pytest

from src.core.config import CrawlConfig, Selectors
from src.infrastructure.checkpoint import CheckpointStore
from src.infrastructure.parser import NoticeParser
from src.infrastructure.repository import NoticeRepository
from src.service.crawler_service import CrawlerService


@dataclass
class StubRepository:  # 저장소 스텁.
    def save_list_items(self, items: list[Any]) -> None:
        return None

    def save_detail_items(self, items: list[Any]) -> None:
        return None

    def save_noce_items(self, items: list[Any]) -> None:
        return None

    def save_attachment_items(self, items: list[Any]) -> None:
        return None

    def save_opening_summary_items(self, items: list[Any]) -> None:
        return None

    def save_opening_result_items(self, items: list[Any]) -> None:
        return None


@dataclass
class StubParser:  # 파서 스텁.
    def parse_list(self, page: Any) -> list[dict[str, Any]]:
        return []


def _build_service(
    tmp_path: Any,
    payload: dict[str, Any],
    search_range_days: int | None = None,
) -> CrawlerService:
    config = CrawlConfig(
        base_url="https://example.com",
        list_url="https://example.com/list",
        detail_api_url="https://example.com/detail",
        max_pages=1,
        timeout_ms=5000,
        retry_count=1,
        retry_backoff_sec=0.1,
        user_agent="test-agent",
        search_range_days=search_range_days,
        list_api_payload=payload,
        selectors=Selectors(list_row="#list tr", list_link="#list a"),
    )
    repo = cast(NoticeRepository, StubRepository())
    parser = cast(NoticeParser, StubParser())
    checkpoint = CheckpointStore(str(tmp_path / "checkpoint.json"))
    return CrawlerService(config, repo, parser, checkpoint)


def test_build_list_payload_dynamic_range(tmp_path: Any) -> None:
    payload = {
        "pbancPstgStDt": "20260101",
        "pbancPstgEdDt": "20260102",
        "onbsPrnmntStDt": "20260101",
        "onbsPrnmntEdDt": "20260102",
        "recordCountPerPage": "100",
    }
    service = _build_service(tmp_path, payload, search_range_days=3)

    built = service._build_list_payload(1)

    today = datetime.now().date()
    start_date = today - timedelta(days=2)
    assert built["pbancPstgStDt"] == start_date.strftime("%Y%m%d")
    assert built["pbancPstgEdDt"] == today.strftime("%Y%m%d")
    assert built["onbsPrnmntStDt"] == start_date.strftime("%Y%m%d")
    assert built["onbsPrnmntEdDt"] == today.strftime("%Y%m%d")


def test_build_list_payload_invalid_format(tmp_path: Any) -> None:
    payload = {
        "pbancPstgStDt": "2026-01-01",
        "pbancPstgEdDt": "20260102",
        "recordCountPerPage": "100",
    }
    service = _build_service(tmp_path, payload)

    with pytest.raises(ValueError):
        service._build_list_payload(1)


def test_build_list_payload_invalid_order(tmp_path: Any) -> None:
    payload = {
        "pbancPstgStDt": "20260210",
        "pbancPstgEdDt": "20260209",
        "recordCountPerPage": "100",
    }
    service = _build_service(tmp_path, payload)

    with pytest.raises(ValueError):
        service._build_list_payload(1)
