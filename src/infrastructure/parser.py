from __future__ import annotations

import logging
from typing import Any

from src.core.config import Selectors


class NoticeParser:
    """현재는 Playwright DOM 기반이며, Selectolax 도입은 추후 계획."""

    def __init__(self, selectors: Selectors) -> None:
        self._selectors = selectors
        self._logger = logging.getLogger("parser")

    def parse_list(self, page: Any) -> list[Any]:
        rows = page.locator(self._selectors.list_row)
        row_count = rows.count()
        items: list[dict[str, str]] = []
        for idx in range(row_count):
            row = rows.nth(idx)
            cell_map: dict[str, str] = {}
            cells = row.locator("td[col_id]")
            for cidx in range(cells.count()):
                cell = cells.nth(cidx)
                col_id = cell.get_attribute("col_id")
                if not col_id:
                    continue
                text = cell.inner_text().strip()
                cell_map[col_id] = text
            if cell_map:
                items.append(cell_map)
        self._logger.info("parsed_list_rows=%s", len(items))
        return items

    def parse_detail(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        detail = result.get("bidPbancMap", {})
        if not isinstance(detail, dict):
            self._logger.warning("detail_payload_invalid")
            return {}
        self._logger.info("parsed_detail_keys=%s", len(detail))
        return detail

    def parse_noce(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        items = result.get("noceList", [])
        if not isinstance(items, list):
            self._logger.warning("noce_payload_invalid")
            return []
        self._logger.info("parsed_noce_rows=%s", len(items))
        return items

    def parse_opening(self, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        summary = result.get("pbancMap", {})
        rows = result.get("oobsRsltList", [])
        if not isinstance(summary, dict):
            summary = {}
        if not isinstance(rows, list):
            rows = []
        self._logger.info("parsed_opening summary_keys=%s rows=%s", len(summary), len(rows))
        return summary, rows

    def parse_attachments(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        result = payload.get("dlUntyAtchFileL", []) if isinstance(payload, dict) else []
        if not isinstance(result, list):
            self._logger.warning("attachment_payload_invalid")
            return []
        self._logger.info("parsed_attachment_rows=%s", len(result))
        return result
