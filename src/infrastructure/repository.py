from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Iterable

from src.domain.models import (
    AttachmentItem,
    BidNoticeDetail,
    BidNoticeListItem,
    BidOpeningResult,
    BidOpeningSummary,
    NoceItem,
)

_LIST_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord")
_DETAIL_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord")
_NOCE_UNIQUE_KEYS = ("pst_no", "bbs_no")
_ATTACH_UNIQUE_KEYS = ("unty_atch_file_no", "atch_file_sqno")
_OPENING_SUMMARY_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord")
_OPENING_RESULT_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord", "ibx_onbs_rnkg")


class NoticeRepository:
    """현재는 CSV 저장소이며, SQLite 저장은 추후 도입 예정이다."""
    def __init__(self, sqlite_path: str) -> None:
        self._sqlite_path = sqlite_path
        self._logger = logging.getLogger("repository")
        self._data_dir = Path(sqlite_path).parent
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._list_path = self._data_dir / "list.csv"
        self._detail_path = self._data_dir / "detail.csv"
        self._noce_path = self._data_dir / "notice.csv"
        self._attachment_path = self._data_dir / "attachments.csv"
        self._opening_summary_path = self._data_dir / "opening_summary.csv"
        self._opening_result_path = self._data_dir / "opening_result.csv"
        self._list_seen = self._load_seen(self._list_path, _LIST_UNIQUE_KEYS)
        self._detail_seen = self._load_seen(self._detail_path, _DETAIL_UNIQUE_KEYS)
        self._noce_seen = self._load_seen(self._noce_path, _NOCE_UNIQUE_KEYS)
        self._attachment_seen = self._load_seen(self._attachment_path, _ATTACH_UNIQUE_KEYS)
        self._opening_summary_seen = self._load_seen(
            self._opening_summary_path, _OPENING_SUMMARY_UNIQUE_KEYS
        )
        self._opening_result_seen = self._load_seen(
            self._opening_result_path, _OPENING_RESULT_UNIQUE_KEYS
        )

    def save_list_items(self, items: Iterable[BidNoticeListItem]) -> None:
        rows = self._dedupe_rows([item.model_dump() for item in items], _LIST_UNIQUE_KEYS, self._list_seen)
        self._write_csv(self._list_path, rows, BidNoticeListItem)

    def save_detail_items(self, items: Iterable[BidNoticeDetail]) -> None:
        rows = self._dedupe_rows([item.model_dump() for item in items], _DETAIL_UNIQUE_KEYS, self._detail_seen)
        self._write_csv(self._detail_path, rows, BidNoticeDetail)

    def save_noce_items(self, items: Iterable[NoceItem]) -> None:
        rows = self._dedupe_rows([item.model_dump() for item in items], _NOCE_UNIQUE_KEYS, self._noce_seen)
        self._write_csv(self._noce_path, rows, NoceItem)

    def save_attachment_items(self, items: Iterable[AttachmentItem]) -> None:
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _ATTACH_UNIQUE_KEYS, self._attachment_seen
        )
        self._write_csv(self._attachment_path, rows, AttachmentItem)

    def save_opening_summary_items(self, items: Iterable[BidOpeningSummary]) -> None:
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _OPENING_SUMMARY_UNIQUE_KEYS, self._opening_summary_seen
        )
        self._write_csv(self._opening_summary_path, rows, BidOpeningSummary)

    def save_opening_result_items(self, items: Iterable[BidOpeningResult]) -> None:
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _OPENING_RESULT_UNIQUE_KEYS, self._opening_result_seen
        )
        self._write_csv(self._opening_result_path, rows, BidOpeningResult)

    def _write_csv(self, path: Path, rows: list[dict[str, Any]], model_type: type) -> None:
        if not rows:
            return
        fieldnames = list(model_type.model_fields.keys())
        file_exists = path.exists()
        with path.open("a", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key) for key in fieldnames})
        self._logger.info("CSV 저장 완료 경로=%s 행=%s", path, len(rows))

    def _load_seen(self, path: Path, keys: tuple[str, ...]) -> set[tuple[str, ...]]:
        if not path.exists():
            return set()
        seen: set[tuple[str, ...]] = set()
        with path.open("r", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                key = tuple((row.get(k) or "").strip() for k in keys)
                seen.add(key)
        return seen

    def _dedupe_rows(
        self,
        rows: list[dict[str, Any]],
        keys: tuple[str, ...],
        seen: set[tuple[str, ...]],
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        unique_rows: list[dict[str, Any]] = []
        skipped = 0
        for row in rows:
            key = tuple((str(row.get(k) or "")).strip() for k in keys)
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            unique_rows.append(row)
        if skipped:
            self._logger.info("중복 건너뜀 키=%s 건수=%s", keys, skipped)
        return unique_rows
