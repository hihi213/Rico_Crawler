from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import csv  # CSV 저장용.
import logging  # 로깅.
from pathlib import Path  # 경로 처리.
from typing import Any, Iterable  # 범용 타입.

from src.domain.models import BidNoticeDetail, BidNoticeListItem  # 도메인 모델.


class NoticeRepository:  # 저장소 인터페이스.
    def __init__(self, sqlite_path: str) -> None:  # DB 경로 주입.
        self._sqlite_path = sqlite_path  # 경로 보관
        self._logger = logging.getLogger("repository")  # 로거 생성.
        self._data_dir = Path(sqlite_path).parent  # CSV 저장 경로. 파일 경로에서 '파일 이름'을 떼어내고 '폴더 경로'만 추출
        self._data_dir.mkdir(parents=True, exist_ok=True)  # 폴더 생성.
        self._list_path = self._data_dir / "bid_notice_list.csv"  # 목록 CSV.
        self._detail_path = self._data_dir / "bid_notice_detail.csv"  # 상세 CSV.

    def save_list_items(self, items: Iterable[BidNoticeListItem]) -> None:  # 목록 저장.
        rows = [item.model_dump() for item in items]  # Pydantic 모델을 dict로 변환.
        self._write_csv(self._list_path, rows, BidNoticeListItem)  # CSV 저장.

    def save_detail_items(self, items: Iterable[BidNoticeDetail]) -> None:  # 상세 저장.
        rows = [item.model_dump() for item in items]  # Pydantic 모델을 dict로 변환.
        self._write_csv(self._detail_path, rows, BidNoticeDetail)  # CSV 저장.

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
