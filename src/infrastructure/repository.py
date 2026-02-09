from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import csv  # CSV 저장용.
import logging  # 로깅.
from pathlib import Path  # 경로 처리.
from typing import Any, Iterable  # 범용 타입.

from src.domain.models import (  # 도메인 모델.
    AttachmentItem,
    BidNoticeDetail,
    BidNoticeListItem,
    BidOpeningResult,
    BidOpeningSummary,
    NoceItem,
)

_LIST_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord")  # 목록 중복 기준.
_DETAIL_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord")  # 상세 중복 기준.
_NOCE_UNIQUE_KEYS = ("pst_no", "bbs_no")  # 공지 중복 기준.
_ATTACH_UNIQUE_KEYS = ("unty_atch_file_no", "atch_file_sqno")  # 첨부 중복 기준.
_OPENING_SUMMARY_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord")  # 개찰 요약.
_OPENING_RESULT_UNIQUE_KEYS = ("bid_pbanc_no", "bid_pbanc_ord", "bid_clsf_no", "bid_prgrs_ord", "ibx_onbs_rnkg")  # 개찰 결과.


class NoticeRepository:  # 저장소 인터페이스.
    def __init__(self, sqlite_path: str) -> None:  # DB 경로 주입.
        self._sqlite_path = sqlite_path  # 경로 보관
        self._logger = logging.getLogger("repository")  # 로거 생성.
        self._data_dir = Path(sqlite_path).parent  # CSV 저장 경로. 파일 경로에서 '파일 이름'을 떼어내고 '폴더 경로'만 추출
        self._data_dir.mkdir(parents=True, exist_ok=True)  # 폴더 생성.
        self._list_path = self._data_dir / "bid_notice_list.csv"  # 목록 CSV.
        self._detail_path = self._data_dir / "bid_notice_detail.csv"  # 상세 CSV.
        self._noce_path = self._data_dir / "bid_notice_noce.csv"  # 공지 CSV.
        self._attachment_path = self._data_dir / "bid_notice_attachment.csv"  # 첨부 CSV.
        self._opening_summary_path = self._data_dir / "bid_opening_summary.csv"  # 개찰 요약 CSV.
        self._opening_result_path = self._data_dir / "bid_opening_result.csv"  # 개찰 결과 CSV.
        self._list_seen = self._load_seen(self._list_path, _LIST_UNIQUE_KEYS)  # 목록 중복 캐시.
        self._detail_seen = self._load_seen(self._detail_path, _DETAIL_UNIQUE_KEYS)  # 상세 중복 캐시.
        self._noce_seen = self._load_seen(self._noce_path, _NOCE_UNIQUE_KEYS)  # 공지 중복 캐시.
        self._attachment_seen = self._load_seen(self._attachment_path, _ATTACH_UNIQUE_KEYS)  # 첨부 중복 캐시.
        self._opening_summary_seen = self._load_seen(
            self._opening_summary_path, _OPENING_SUMMARY_UNIQUE_KEYS
        )  # 개찰 요약 중복 캐시.
        self._opening_result_seen = self._load_seen(
            self._opening_result_path, _OPENING_RESULT_UNIQUE_KEYS
        )  # 개찰 결과 중복 캐시.

    def save_list_items(self, items: Iterable[BidNoticeListItem]) -> None:  # 목록 저장.
        rows = self._dedupe_rows([item.model_dump() for item in items], _LIST_UNIQUE_KEYS, self._list_seen)
        self._write_csv(self._list_path, rows, BidNoticeListItem)  # CSV 저장.

    def save_detail_items(self, items: Iterable[BidNoticeDetail]) -> None:  # 상세 저장.
        rows = self._dedupe_rows([item.model_dump() for item in items], _DETAIL_UNIQUE_KEYS, self._detail_seen)
        self._write_csv(self._detail_path, rows, BidNoticeDetail)  # CSV 저장.

    def save_noce_items(self, items: Iterable[NoceItem]) -> None:  # 공지 저장.
        rows = self._dedupe_rows([item.model_dump() for item in items], _NOCE_UNIQUE_KEYS, self._noce_seen)
        self._write_csv(self._noce_path, rows, NoceItem)

    def save_attachment_items(self, items: Iterable[AttachmentItem]) -> None:  # 첨부 저장.
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _ATTACH_UNIQUE_KEYS, self._attachment_seen
        )
        self._write_csv(self._attachment_path, rows, AttachmentItem)

    def save_opening_summary_items(self, items: Iterable[BidOpeningSummary]) -> None:  # 개찰 요약 저장.
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _OPENING_SUMMARY_UNIQUE_KEYS, self._opening_summary_seen
        )
        self._write_csv(self._opening_summary_path, rows, BidOpeningSummary)

    def save_opening_result_items(self, items: Iterable[BidOpeningResult]) -> None:  # 개찰 결과 저장.
        rows = self._dedupe_rows(
            [item.model_dump() for item in items], _OPENING_RESULT_UNIQUE_KEYS, self._opening_result_seen
        )
        self._write_csv(self._opening_result_path, rows, BidOpeningResult)

    def _write_csv(  # CSV 저장 공통 처리.
        self,
        path: Path,  # 파일 경로.
        rows: list[dict[str, Any]],  # 저장할 행.
        model_type: type,  # 컬럼 정의 모델.
    ) -> None:
        if not rows:  # 저장할 내용이 없으면.
            return  # 종료.
        fieldnames = list(model_type.model_fields.keys())  # 컬럼 순서 고정.
        file_exists = path.exists()  # 파일 존재 여부.
        with path.open("a", newline="", encoding="utf-8") as fp:  # append 모드.
            writer = csv.DictWriter(fp, fieldnames=fieldnames)  # CSV writer.
            if not file_exists:  # 파일이 없으면.
                writer.writeheader()  # 헤더 작성.
            for row in rows:  # 각 행 저장.
                writer.writerow({key: row.get(key) for key in fieldnames})  # 순서 고정 저장.
        self._logger.info("csv_saved path=%s rows=%s", path, len(rows))  # 저장 로그.

    def _load_seen(self, path: Path, keys: tuple[str, ...]) -> set[tuple[str, ...]]:  # 기존 중복 키 로드.
        if not path.exists():  # 파일 없으면.
            return set()  # 빈 세트.
        seen: set[tuple[str, ...]] = set()  # 중복 캐시.
        with path.open("r", newline="", encoding="utf-8") as fp:  # CSV 읽기.
            reader = csv.DictReader(fp)  # 헤더 기반 읽기.
            for row in reader:  # 각 행 처리.
                key = tuple((row.get(k) or "").strip() for k in keys)  # 키 조합.
                seen.add(key)  # 캐시 추가.
        return seen  # 캐시 반환.

    def _dedupe_rows(  # 중복 제거.
        self,
        rows: list[dict[str, Any]],
        keys: tuple[str, ...],
        seen: set[tuple[str, ...]],
    ) -> list[dict[str, Any]]:
        if not rows:  # 저장할 내용이 없으면.
            return []  # 빈 리스트.
        unique_rows: list[dict[str, Any]] = []  # 결과 리스트.
        for row in rows:  # 각 행 확인.
            key = tuple((str(row.get(k) or "")).strip() for k in keys)  # 키 조합.
            if key in seen:  # 중복이면.
                continue  # 스킵.
            seen.add(key)  # 신규 키 등록.
            unique_rows.append(row)  # 결과 추가.
        return unique_rows  # 결과 반환.
