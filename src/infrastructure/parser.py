from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import logging  # 로깅.
from typing import Any  # 범용 타입.

from src.core.config import Selectors  # 셀렉터 설정 모델.


class NoticeParser:  # 파싱 로직 인터페이스.
    def __init__(self, selectors: Selectors) -> None:  # 셀렉터(CSS 선택자 모음) 주입.
        self._selectors = selectors  # 셀렉터 보관.
        self._logger = logging.getLogger("parser")  # 로거 생성.

    def parse_list(self, page: Any) -> list[Any]:  # 목록 파싱.
        rows = page.locator(self._selectors.list_row)  # 목록 행 로케이터.
        row_count = rows.count()  # 행 수.
        items: list[dict[str, str]] = []  # 원본 행 데이터 저장할 빈 객체
        for idx in range(row_count):  # 행 순회.
            row = rows.nth(idx)  # 현재 행의 위치
            cell_map: dict[str, str] = {}  # 이번 줄의 데이터를 담을 맵(HashMap) 생성(col_id 기반 필드 맵.)
            cells = row.locator("td[col_id]")  # col_id가 있는 셀만 수집.
            for cidx in range(cells.count()):  # 셀 순회.
                cell = cells.nth(cidx)  # 현재 셀.
                col_id = cell.get_attribute("col_id")  # col_id 추출.
                if not col_id:  # col_id가 없으면 스킵.
                    continue  # 다음 셀.
                text = cell.inner_text().strip()  # 셀 텍스트 정리.
                cell_map[col_id] = text  # 맵에 저장.
            if cell_map:  # 수집된 값이 있으면.
                items.append(cell_map)  # 결과에 추가.
        self._logger.info("parsed_list_rows=%s", len(items))  # 파싱 결과 로그.
        return items  # 원본 맵 리스트 반환.

    def parse_detail(self, page: Any) -> dict[str, Any]:  # 상세 파싱.
        detail: dict[str, Any] = {}  # 상세 필드 결과.
        fields = self._selectors.detail_fields  # 상세 셀렉터 묶음.
        if fields.budget_amount:  # 예산 셀렉터가 있으면.
            detail["budget_amount"] = (  # 예산 값 저장.
                page.locator(fields.budget_amount).first.inner_text().strip()
            )
        if fields.bid_start_at:  # 시작일 셀렉터가 있으면.
            detail["bid_start_at"] = (  # 시작일 값 저장.
                page.locator(fields.bid_start_at).first.inner_text().strip()
            )
        if fields.bid_end_at:  # 마감일 셀렉터가 있으면.
            detail["bid_end_at"] = (  # 마감일 값 저장.
                page.locator(fields.bid_end_at).first.inner_text().strip()
            )
        self._logger.info("parsed_detail_fields=%s", list(detail.keys()))  # 상세 파싱 로그.
        return detail  # 상세 결과 반환.
