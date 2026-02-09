from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import json  # JSON 직렬화.
import logging  # 로깅.
from datetime import datetime  # 타임스탬프 생성.
from datetime import datetime, timedelta  # 날짜 처리 모듈.
from typing import Any, Optional  # 범용 타입과 선택적 타입.

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from src.core.config import CrawlConfig  # 크롤링 설정 모델.
from src.domain.models import (
    AttachmentItem,
    BidNoticeDetail,
    BidNoticeListItem,
    BidOpeningResult,
    BidOpeningSummary,
    NoceItem,
)  # 도메인 모델.
from src.infrastructure.checkpoint import CheckpointStore, CrawlCheckpoint  # 체크포인트 저장소.
from src.infrastructure.parser import NoticeParser  # 파서 인터페이스.
from src.infrastructure.repository import NoticeRepository  # 저장소 인터페이스.
from src.infrastructure.snapshot import SnapshotStore  # 스냅샷 저장소.


class CrawlerService:  # 크롤링 비즈니스 로직 계층.
    def __init__(  # 의존성 주입.
        self,
        config: CrawlConfig,  # 크롤링 설정.
        repo: NoticeRepository,  # 저장소 구현체.
        parser: NoticeParser,  # 파서 구현체.
        checkpoint: CheckpointStore,  # 체크포인트 저장소.
    ) -> None:
        self._config = config  # 설정 보관.
        self._repo = repo  # 저장소 보관.
        self._parser = parser  # 파서 보관.
        self._checkpoint = checkpoint  # 체크포인트 보관.
        self._logger = logging.getLogger("service")  # 로거 생성.
        self._snapshot = SnapshotStore(config.snapshot_dir) if config.snapshot_enabled else None  # 스냅샷 저장소.

    def run(self, page: Any, max_pages: Optional[int]) -> None:  # 실행 진입점
        target_pages = self._config.max_pages  # 기본 페이지 수.
        if max_pages is not None:  # CLI 제한이 있으면.
            target_pages = min(target_pages, max_pages)  # 매걔변수와 시스템 설정중 더 작은 값 사용.
        start_page = 1  # 시작 페이지.
        saved = self._checkpoint.load()  # 체크포인트 로드.
        if saved is not None:  # 저장된 체크포인트가 있으면.
            start_page = max(1, saved.current_page)  # 저장된 페이지부터 시작.
        self._logger.info("crawl_start pages=%s", target_pages)  # 시작 로그.
        if self._config.list_api_url:  # 목록 API를 쓰는 경우.
            for page_index in range(start_page, target_pages + 1):  # 페이지 반복.
                raw_rows = self._fetch_list_via_api(page, page_index)  # API 목록 호출.
                if self._config.snapshot_only_list:  # 목록만 저장하는 모드면.
                    self._checkpoint.save(CrawlCheckpoint(current_page=page_index + 1))  # 다음 페이지 저장.
                    continue  # 상세 수집 생략.
                items, list_skipped = self._build_list_items(raw_rows)  # 목록 모델 생성.
                items = self._apply_list_filters(items)  # 후처리 필터 적용.
                detail_items: list[BidNoticeDetail] = []  # 상세 모델 리스트.
                opening_summaries: list[BidOpeningSummary] = []  # 개찰 요약 리스트.
                opening_results: list[BidOpeningResult] = []  # 개찰 결과 리스트.
                attachments: list[AttachmentItem] = []  # 첨부 리스트.
                noce_items: list[NoceItem] = []  # 공지 리스트.
                noce_skipped = 0
                attachment_skipped = 0
                opening_summary_skipped = 0
                opening_row_skipped = 0
                for item in items:  # 상세/부가 데이터 수집.
                    detail_raw = self._fetch_detail_via_api(page, item)  # 상세 API 호출.
                    detail_items.append(self._build_detail_from_list(item, detail_raw))  # 상세 모델 생성.
                    noce_batch, noce_skip = self._build_noce_items(page, item)  # 공지 리스트.
                    noce_items.extend(noce_batch)
                    noce_skipped += noce_skip
                    attachment_batch, attachment_skip = self._build_attachment_items(page, detail_raw)  # 첨부 리스트.
                    attachments.extend(attachment_batch)
                    attachment_skipped += attachment_skip
                    opening_summary, opening_rows, sum_skip, row_skip = self._build_opening_items(page, item)
                    opening_summary_skipped += sum_skip
                    opening_row_skipped += row_skip
                    if opening_summary is not None:
                        opening_summaries.append(opening_summary)
                    opening_results.extend(opening_rows)
                if items:  # 저장할 항목이 있으면.
                    self._repo.save_list_items(items)  # 목록 저장.
                if detail_items:  # 상세 항목이 있으면.
                    self._repo.save_detail_items(detail_items)  # 상세 저장.
                if noce_items:  # 공지 저장.
                    self._repo.save_noce_items(noce_items)
                if attachments:  # 첨부 저장.
                    self._repo.save_attachment_items(attachments)
                if opening_summaries:  # 개찰 요약 저장.
                    self._repo.save_opening_summary_items(opening_summaries)
                if opening_results:  # 개찰 결과 저장.
                    self._repo.save_opening_result_items(opening_results)
                self._logger.info(
                    "page_saved page=%s list=%s detail=%s noce=%s attach=%s opening_summary=%s opening_result=%s",
                    page_index,
                    len(items),
                    len(detail_items),
                    len(noce_items),
                    len(attachments),
                    len(opening_summaries),
                    len(opening_results),
                )
                self._logger.info(
                    "page_skipped page=%s list=%s noce=%s attach=%s opening_summary=%s opening_result=%s",
                    page_index,
                    list_skipped,
                    noce_skipped,
                    attachment_skipped,
                    opening_summary_skipped,
                    opening_row_skipped,
                )
                self._checkpoint.save(CrawlCheckpoint(current_page=page_index + 1))  # 다음 페이지 저장.
            self._logger.info("crawl_done")  # 종료 로그.
            return  # API 경로는 여기서 종료.
        page.goto(self._config.list_url, wait_until="networkidle")  # 목록 페이지 이동.
        if self._config.selectors.search_button:  # 검색 버튼이 설정된 경우.
            page.wait_for_selector(self._config.selectors.search_button)  # 검색 버튼 로드 대기.
            page.locator(self._config.selectors.search_button).first.click()  # 검색 실행.
            page.wait_for_load_state("networkidle")  # 검색 결과 로딩 대기.
        page.wait_for_selector(self._config.selectors.list_row)  # 목록 로드 대기.
        for page_index in range(start_page, target_pages + 1):  # 페이지 반복.
            raw_rows = self._parser.parse_list(page)  # 목록 파싱.
            items, list_skipped = self._build_list_items(raw_rows)  # 목록 모델 생성.
            items = self._apply_list_filters(items)  # 후처리 필터 적용.
            detail_items: list[BidNoticeDetail] = []  # 상세 모델 리스트.
            detail_skipped = 0
            for row_index, item in enumerate(items):  # 각 행 변환.
                detail_data: dict[str, Any] = {}  # 상세 원본 맵.
                if self._config.selectors.detail_popup and self._config.selectors.detail_close:  # 상세 설정 확인.
                    detail_data = self._open_detail_and_fetch(page, row_index)  # 상세 응답 확보.
                    self._close_detail(page)  # 상세 팝업 닫기.
                try:
                    detail_item = self._build_detail_from_list(item, detail_data)  # 상세 생성.
                except Exception as exc:
                    self._logger.warning("detail_row_skip err=%s key=%s", exc, item.bid_pbanc_no)
                    detail_skipped += 1
                    continue
                detail_items.append(detail_item)  # 상세 저장 목록에 추가.
            if items:  # 저장할 항목이 있으면.
                self._repo.save_list_items(items)  # 목록 저장.
            if detail_items:  # 상세 항목이 있으면.
                self._repo.save_detail_items(detail_items)  # 상세 저장.
            self._logger.info(
                "page_skipped page=%s list=%s detail=%s", page_index, list_skipped, detail_skipped
            )
            if page_index >= target_pages:  # 마지막 페이지면 종료.
                break  # 루프 종료.
            if not self._config.selectors.pagination_next:  # 다음 버튼 없으면.
                self._logger.info("pagination_selector_missing")  # 로그.
                break  # 종료.
            next_button = page.locator(self._config.selectors.pagination_next)  # 다음 버튼.
            if next_button.count() == 0:  # 버튼이 없으면.
                self._logger.info("pagination_next_missing")  # 로그.
                break  # 종료.
            next_button.first.click()  # 다음 페이지 클릭.
            page.wait_for_load_state("networkidle")  # 로딩 대기.
            page.wait_for_selector(self._config.selectors.list_row)  # 목록 로드 대기.
            self._checkpoint.save(CrawlCheckpoint(current_page=page_index + 1))  # 다음 페이지 저장.
        self._logger.info("crawl_done")  # 종료 로그.

    def _fetch_list_via_api(self, page: Any, current_page: int) -> list[dict[str, Any]]:  # 목록 API 호출.
        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> list[dict[str, Any]]:
            self._logger.info("list_api_call page=%s", current_page)  # 호출 시작 로그.
            payload = self._build_list_payload(current_page)  # 유효성 검증 포함 페이로드 구성.
            resp = page.request.post(  # API 호출.
                self._config.list_api_url,
                data=json.dumps({"dlParamM": payload}),
                headers=self._config.list_api_headers,
            )
            self._logger.info("list_api_response page=%s status=%s", current_page, resp.status)  # 응답 상태 로그.
            body = resp.json()  # JSON 파싱.
            self._maybe_snapshot_list(current_page, body)  # 원본 스냅샷 저장.
            if body.get("ErrorCode") != 0:  # 오류 처리.
                raise RuntimeError(f"list_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            result = body.get("result", [])  # 결과 리스트.
            if not isinstance(result, list):
                raise RuntimeError("list_api_invalid_result")
            return result

        try:
            return _call()
        except Exception as exc:
            self._logger.warning("list_api_skip err=%s page=%s", exc, current_page, exc_info=True)
            return []

    def _build_list_payload(self, current_page: int) -> dict[str, Any]:  # 목록 페이로드 구성.
        payload = dict(self._config.list_api_payload)  # 원본 보호.
        payload["currentPage"] = current_page  # 페이지 갱신.
        search_range = self._config.search_range_days  # 동적 날짜 범위.
        if search_range is not None:  # 동적 날짜 모드면.
            if search_range <= 0:  # 유효성 검사.
                raise ValueError("search_range_days must be positive")  # 잘못된 범위 차단.
            self._apply_date_range(payload, search_range)  # 날짜 계산 적용.
        else:  # 고정 날짜 모드면.
            self._validate_payload_dates(payload)  # 날짜 형식 검증.
        return payload  # 최종 페이로드 반환.

    def _apply_date_range(self, payload: dict[str, Any], days: int) -> None:  # 날짜 범위 적용.
        today = datetime.now().date()  # 기준 날짜(로컬).
        start_date = today - timedelta(days=days - 1)  # 시작일 계산.
        payload["pbancPstgStDt"] = start_date.strftime("%Y%m%d")  # 게시 시작일.
        payload["pbancPstgEdDt"] = today.strftime("%Y%m%d")  # 게시 종료일.
        if "onbsPrnmntStDt" in payload:  # 개찰 시작일 키가 있으면.
            payload["onbsPrnmntStDt"] = start_date.strftime("%Y%m%d")  # 개찰 시작일.
        if "onbsPrnmntEdDt" in payload:  # 개찰 종료일 키가 있으면.
            payload["onbsPrnmntEdDt"] = today.strftime("%Y%m%d")  # 개찰 종료일.

    def _validate_payload_dates(self, payload: dict[str, Any]) -> None:  # 날짜 유효성 검증.
        parsed: dict[str, datetime] = {}  # 파싱된 날짜 보관.
        for key in ("pbancPstgStDt", "pbancPstgEdDt", "onbsPrnmntStDt", "onbsPrnmntEdDt"):  # 날짜 키.
            raw = payload.get(key)  # 원본 값.
            if raw in (None, ""):  # 값이 없으면 스킵.
                continue  # 다음 키로.
            parsed[key] = self._parse_yyyymmdd(str(raw), key)  # 포맷 검증 및 저장.
        self._validate_date_order(parsed, "pbancPstgStDt", "pbancPstgEdDt")  # 게시일 범위 확인.
        self._validate_date_order(parsed, "onbsPrnmntStDt", "onbsPrnmntEdDt")  # 개찰일 범위 확인.

    def _validate_yyyymmdd(self, value: str, field_name: str) -> None:  # 날짜 포맷 검증.
        self._parse_yyyymmdd(value, field_name)  # 파싱 가능 여부만 확인.

    def _parse_yyyymmdd(self, value: str, field_name: str) -> datetime:  # 날짜 파싱.
        try:  # 파싱 시도.
            return datetime.strptime(value, "%Y%m%d")  # YYYYMMDD 형식 확인.
        except ValueError as exc:  # 잘못된 날짜 포맷.
            raise ValueError(f"Invalid date for {field_name}: {value}") from exc  # 명확한 에러.

    def _validate_date_order(self, parsed: dict[str, datetime], start_key: str, end_key: str) -> None:  # 순서 검증.
        if start_key not in parsed or end_key not in parsed:  # 둘 중 하나라도 없으면.
            return  # 검증 생략.
        if parsed[start_key] > parsed[end_key]:  # 시작일이 종료일보다 늦으면.
            raise ValueError(f"{start_key} must be <= {end_key}")  # 범위 오류.

    def _build_list_items(  # 목록 모델 생성.
        self, raw_rows: list[dict[str, Any]]
    ) -> tuple[list[BidNoticeListItem], int]:
        items: list[BidNoticeListItem] = []  # 변환된 모델 리스트.
        skipped = 0
        for raw in raw_rows:  # 각 행 변환.
            mapped = self._map_list_row(raw)  # 필드 매핑.
            try:  # 검증 실패를 대비.
                list_item = BidNoticeListItem(**mapped)  # 모델 생성.
                items.append(list_item)  # 목록 추가.
            except Exception as exc:  # 검증 실패.
                self._logger.warning("list_row_skip err=%s raw=%s", exc, raw)  # 스킵 로그.
                skipped += 1
                continue  # 다음 행.
        return items, skipped

    def _apply_list_filters(self, items: list[BidNoticeListItem]) -> list[BidNoticeListItem]:  # 목록 필터.
        filtered = items  # 기본은 전체.
        if self._config.list_filter_pbanc_knd_cd:  # 공고종류 필터가 있으면.
            filtered = [
                item for item in filtered if item.pbanc_knd_cd == self._config.list_filter_pbanc_knd_cd
            ]
        if self._config.list_filter_pbanc_stts_cd:  # 공고구분 필터가 있으면.
            filtered = [
                item for item in filtered if item.pbanc_stts_cd == self._config.list_filter_pbanc_stts_cd
            ]
        if self._config.list_filter_bid_pbanc_pgst_cd:  # 진행상태 필터가 있으면.
            filtered = [
                item
                for item in filtered
                if item.bid_pbanc_pgst_cd == self._config.list_filter_bid_pbanc_pgst_cd
            ]
        if len(filtered) != len(items):  # 필터로 줄어들었으면.
            self._logger.info("list_filtered before=%s after=%s", len(items), len(filtered))
        return filtered

    def _fetch_detail_via_api(self, page: Any, item: BidNoticeListItem) -> dict[str, Any]:  # 상세 API 호출.
        if not self._config.detail_api_url:  # 설정이 없으면.
            return {}  # 빈 결과.
        payload = dict(self._config.detail_api_payload)  # 원본 보호.
        payload.update(  # 필수 키 채우기.
            {
                "bidPbancNo": item.bid_pbanc_no,
                "bidPbancOrd": item.bid_pbanc_ord,
                "bidClsfNo": item.bid_clsf_no or "",
                "bidPrgrsOrd": item.bid_prgrs_ord or "",
                "pstNo": item.bid_pbanc_no,
            }
        )

        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> dict[str, Any]:
            resp = page.request.post(
                self._config.detail_api_url,
                data=json.dumps({"dlSrchCndtM": payload}),
                headers=self._config.detail_api_headers,
            )
            body = resp.json()
            self._maybe_snapshot_detail(item, body)  # 미확정 항목이 있으면 스냅샷 저장.
            if body.get("ErrorCode") != 0:
                raise RuntimeError(f"detail_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            return self._parser.parse_detail(body)

        try:
            return _call()
        except Exception as exc:
            self._logger.warning("detail_api_skip err=%s key=%s", exc, item.bid_pbanc_no)
            return {}

    def _build_noce_items(self, page: Any, item: BidNoticeListItem) -> tuple[list[NoceItem], int]:
        if not self._config.noce_api_url:
            return [], 0
        payload = dict(self._config.noce_api_payload)
        payload.update(
            {
                "bidPbancNo": item.bid_pbanc_no,
                "bidPbancOrd": item.bid_pbanc_ord,
                "bidClsfNo": item.bid_clsf_no or "",
                "bidPrgrsOrd": item.bid_prgrs_ord or "",
                "pstNo": item.bid_pbanc_no,
            }
        )

        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> list[dict[str, Any]]:
            resp = page.request.post(
                self._config.noce_api_url,
                data=json.dumps({"dlSrchCndtM": payload}),
                headers=self._config.noce_api_headers,
            )
            body = resp.json()
            if body.get("ErrorCode") != 0:
                raise RuntimeError(f"noce_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            return self._parser.parse_noce(body)

        try:
            rows = _call()
        except Exception as exc:
            self._logger.warning("noce_api_skip err=%s key=%s", exc, item.bid_pbanc_no)
            return [], 0
        results: list[NoceItem] = []
        skipped = 0
        for row in rows:
            mapped = {
                "pst_no": row.get("pstNo"),
                "bbs_no": row.get("bbsNo"),
                "pst_nm": row.get("pstNm"),
                "unty_atch_file_no": row.get("untyAtchFileNo"),
                "use_yn": row.get("useYn"),
                "inpt_dt": row.get("inptDt"),
                "odn3_col_cn": row.get("odn3ColCn"),
                "bulk_pst_cn": row.get("bulkPstCn"),
            }
            try:
                results.append(NoceItem(**mapped))
            except Exception as exc:
                self._logger.warning("noce_row_skip err=%s raw=%s", exc, row)
                skipped += 1
        return results, skipped

    def _build_attachment_items(
        self, page: Any, detail_raw: dict[str, Any]
    ) -> tuple[list[AttachmentItem], int]:
        if not self._config.attachment_api_url:
            return [], 0
        unty_atch_file_no = detail_raw.get("untyAtchFileNo")
        if not unty_atch_file_no:
            return [], 0
        payload = dict(self._config.attachment_api_payload)
        payload["untyAtchFileNo"] = unty_atch_file_no

        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> list[dict[str, Any]]:
            resp = page.request.post(
                self._config.attachment_api_url,
                data=json.dumps({"dlUntyAtchFileM": payload}),
                headers=self._config.attachment_api_headers,
            )
            body = resp.json()
            if body.get("ErrorCode") != 0:
                raise RuntimeError(
                    f"attachment_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}"
                )
            return self._parser.parse_attachments(body)

        try:
            rows = _call()
        except Exception as exc:
            self._logger.warning("attachment_api_skip err=%s key=%s", exc, unty_atch_file_no)
            return [], 0
        results: list[AttachmentItem] = []
        skipped = 0
        for row in rows:
            mapped = {
                "unty_atch_file_no": row.get("untyAtchFileNo"),
                "atch_file_sqno": row.get("atchFileSqno"),
                "bsne_clsf_cd": row.get("bsneClsfCd"),
                "atch_file_knd_cd": row.get("atchFileKndCd"),
                "atch_file_nm": row.get("atchFileNm"),
                "orgnl_atch_file_nm": row.get("orgnlAtchFileNm"),
                "file_extn_nm": row.get("fileExtnNm"),
                "file_sz": row.get("fileSz"),
                "encr_bef_file_sz": row.get("encrBefFileSz"),
                "img_url": row.get("imgUrl"),
                "atch_file_dscr": row.get("atchFileDscr"),
                "mcsc_chck_id_val": row.get("mcscChckIdVal"),
                "dwnld_prms_yn": row.get("dwnldPrmsYn"),
                "kbrdr_id": row.get("kbrdrId"),
                "kbrdr_nm": row.get("kbrdrNm"),
                "inpt_dt": row.get("inptDt"),
                "atch_file_path_nm": row.get("atchFilePathNm"),
                "tbl_nm": row.get("tblNm"),
                "col_nm": row.get("colNm"),
                "atch_file_rmrk_cn": row.get("atchFileRmrkCn"),
            }
            try:
                results.append(AttachmentItem(**mapped))
            except Exception as exc:
                self._logger.warning("attachment_row_skip err=%s raw=%s", exc, row)
                skipped += 1
        return results, skipped

    def _build_opening_items(
        self, page: Any, item: BidNoticeListItem
    ) -> tuple[Optional[BidOpeningSummary], list[BidOpeningResult], int, int]:  # 개찰 항목 생성.
        if not self._config.opening_api_url:
            return None, [], 0, 0
        if not item.bid_clsf_no or not item.bid_prgrs_ord:
            return None, [], 0, 0
        payload = dict(self._config.opening_api_payload)
        payload.update(
            {
                "bidPbancNo": item.bid_pbanc_no,
                "bidPbancOrd": item.bid_pbanc_ord,
                "bidClsfNo": item.bid_clsf_no,
                "bidPrgrsOrd": item.bid_prgrs_ord,
            }
        )

        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> tuple[dict[str, Any], list[dict[str, Any]]]:
            resp = page.request.post(
                self._config.opening_api_url,
                data=json.dumps({"dlSrchCndtM": payload}),
                headers=self._config.opening_api_headers,
            )
            body = resp.json()
            self._maybe_snapshot_opening(item, body)  # 미확정 항목이 있으면 스냅샷 저장.
            if body.get("ErrorCode") != 0:
                raise RuntimeError(f"opening_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            return self._parser.parse_opening(body)

        try:
            summary_raw, rows_raw = _call()
        except Exception as exc:
            self._logger.warning("opening_api_skip err=%s key=%s", exc, item.bid_pbanc_no)
            return None, [], 0, 0
        summary = None
        summary_skipped = 0
        if summary_raw:
            mapped = self._map_opening_summary(summary_raw)
            try:
                summary = BidOpeningSummary(**mapped)
            except Exception as exc:
                self._logger.warning("opening_summary_skip err=%s raw=%s", exc, summary_raw)
                summary_skipped += 1
        results: list[BidOpeningResult] = []
        row_skipped = 0
        for row in rows_raw:
            mapped = self._map_opening_result(row)
            try:
                results.append(BidOpeningResult(**mapped))
            except Exception as exc:
                self._logger.warning("opening_row_skip err=%s raw=%s", exc, row)
                row_skipped += 1
        return summary, results, summary_skipped, row_skipped

    def _map_opening_summary(self, raw: dict[str, Any]) -> dict[str, Any]:  # 개찰 요약 매핑.
        mapping = {
            "bidPbancNo": "bid_pbanc_no",
            "bidPbancOrd": "bid_pbanc_ord",
            "bidClsfNo": "bid_clsf_no",
            "bidPrgrsOrd": "bid_prgrs_ord",
            "bidPbancNm": "bid_pbanc_nm",
            "bidPbancNum": "bid_pbanc_num",
            "pbancSttsCd": "pbanc_stts_cd",
            "pbancSttsCdNm": "pbanc_stts_cd_nm",
            "prcmBsneSeCd": "prcm_bsne_se_cd",
            "prcmBsneSeCdNm": "prcm_bsne_se_cd_nm",
            "bidMthdCd": "bid_mthd_cd",
            "bidMthdCdNm": "bid_mthd_cd_nm",
            "stdCtrtMthdCd": "std_ctrt_mthd_cd",
            "stdCtrtMthdCdNm": "std_ctrt_mthd_cd_nm",
            "scsbdMthdCd": "scsbd_mthd_cd",
            "scsbdMthdCdNm": "scsbd_mthd_cd_nm",
            "pbancInstUntyGrpNo": "pbanc_inst_unty_grp_no",
            "pbancInstUntyGrpNoNm": "pbanc_inst_unty_grp_no_nm",
            "grpNm": "grp_nm",
            "bidBlffId": "bid_blff_id",
            "bidBlffIdNm": "bid_blff_id_nm",
            "ibxOnbsPrnmntDt": "ibx_onbs_prnmnt_dt",
            "ibxOnbsDt": "ibx_onbs_dt",
            "edocNo": "edoc_no",
            "usrDocNoVal": "usr_doc_no_val",
        }
        mapped: dict[str, Any] = {}
        for key, value in raw.items():
            target = mapping.get(key)
            if target:
                mapped[target] = value
        return mapped

    def _map_opening_result(self, raw: dict[str, Any]) -> dict[str, Any]:  # 개찰 결과 매핑.
        mapping = {
            "bidPbancNo": "bid_pbanc_no",
            "bidPbancOrd": "bid_pbanc_ord",
            "bidClsfNo": "bid_clsf_no",
            "bidPrgrsOrd": "bid_prgrs_ord",
            "ibxOnbsRnkg": "ibx_onbs_rnkg",
            "ibxGrpNm": "ibx_grp_nm",
            "ibxBdngAmt": "ibx_bdng_amt",
            "ibxSlprRcptnDt": "ibx_slpr_rcptn_dt",
            "ibxBzmnRegNo": "ibx_bzmn_reg_no",
            "ibxRprsvNm": "ibx_rprsv_nm",
            "bidrPrsnNo": "bidr_prsn_no",
            "bidrPrsnNm": "bidr_prsn_nm",
            "bidUfnsRsnCd": "bid_ufns_rsn_cd",
            "bidUfnsRsnNm": "bid_ufns_rsn_nm",
            "ufnsYn": "ufns_yn",
            "ibxEvlScrPrpl": "ibx_evl_scr_prpl",
            "ibxEvlScrPrce": "ibx_evl_scr_prce",
            "ibxEvlScrOvrl": "ibx_evl_scr_ovrl",
            "sfbrSlctnOrd": "sfbr_slctn_ord",
            "sfbrSlctnRsltCd": "sfbr_slctn_rslt_cd",
        }
        mapped: dict[str, Any] = {}
        for key, value in raw.items():
            target = mapping.get(key)
            if target:
                mapped[target] = value
            if key == "ibxEvlScrPrpl":
                mapped["ibx_evl_scr_prpl_num"] = value
            if key == "ibxEvlScrPrce":
                mapped["ibx_evl_scr_prce_num"] = value
            if key == "ibxEvlScrOvrl":
                mapped["ibx_evl_scr_ovrl_num"] = value
        return mapped

    def _open_detail_and_fetch(self, page: Any, index: int) -> dict[str, Any]:  # 상세 팝업 열기.
        @retry(
            stop=stop_after_attempt(self._config.retry_count),
            wait=wait_fixed(self._config.retry_backoff_sec),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call() -> dict[str, Any]:
            link = page.locator(self._config.selectors.list_link).nth(index)  # 해당 행 링크.
            with page.expect_response(  # 상세 API 응답 대기.
                lambda response: response.url == self._config.detail_api_url
                and response.request.method == "POST"
            ) as response_info:
                link.click()  # 상세 클릭.
            page.wait_for_selector(self._config.selectors.detail_popup)  # 팝업 로드 대기.
            payload = response_info.value.json()  # 응답 JSON 파싱.
            return self._parser.parse_detail(payload)  # 상세 원본 맵 반환.

        try:
            return _call()
        except Exception as exc:
            self._logger.warning("detail_fetch_skip err=%s index=%s", exc, index)
            return {}

    def _close_detail(self, page: Any) -> None:  # 상세 팝업 닫기.
        close_btn = page.locator(self._config.selectors.detail_close).first  # 닫기 버튼.
        close_btn.click()  # 팝업 닫기.
        page.wait_for_timeout(300)  # DOM 반영 대기.

    def _map_list_row(self, raw: dict[str, Any]) -> dict[str, Any]:  # 목록 필드 매핑.
        mapping = {  # col_id -> snake_case.
            "bidPbancNo": "bid_pbanc_no",
            "bidPbancOrd": "bid_pbanc_ord",
            "bidPbancNm": "bid_pbanc_nm",
            "bidPbancNum": "bid_pbanc_num",
            "pbancSttsCd": "pbanc_stts_cd",
            "pbancSttsCdNm": "pbanc_stts_cd_nm",
            "prcmBsneSeCd": "prcm_bsne_se_cd",
            "prcmBsneSeCdNm": "prcm_bsne_se_cd_nm",
            "bidMthdCd": "bid_mthd_cd",
            "bidMthdCdNm": "bid_mthd_cd_nm",
            "stdCtrtMthdCd": "std_ctrt_mthd_cd",
            "stdCtrtMthdCdNm": "std_ctrt_mthd_cd_nm",
            "scsbdMthdCd": "scsbd_mthd_cd",
            "scsbdMthdCdNm": "scsbd_mthd_cd_nm",
            "pbancPstgDt": "pbanc_pstg_dt",
            "pbancKndCd": "pbanc_knd_cd",
            "pbancKndCdNm": "pbanc_knd_cd_nm",
            "grpNm": "grp_nm",
            "slprRcptDdlnDt": "slpr_rcpt_ddln_dt",
            "pbancSttsGridCdNm": "pbanc_stts_grid_cd_nm",
            "rowNum": "row_num",
            "totCnt": "tot_cnt",
            "currentPage": "current_page",
            "recordCountPerPage": "record_count_per_page",
            "nextRowYn": "next_row_yn",
            "edocNo": "edoc_no",
            "usrDocNoVal": "usr_doc_no_val",
            "pbancInstUntyGrpNo": "pbanc_inst_unty_grp_no",
            "pbancPstgYn": "pbanc_pstg_yn",
            "pbancDscrTrgtYn": "pbanc_dscr_trgt_yn",
            "slprRcptBgngYn": "slpr_rcpt_bgng_yn",
            "slprRcptDdlnYn": "slpr_rcpt_ddln_yn",
            "onbsPrnmntYn": "onbs_prnmnt_yn",
            "bidQlfcEndYn": "bid_qlfc_end_yn",
            "pbancBfssYn": "pbanc_bfss_yn",
            "bidClsfNo": "bid_clsf_no",
            "bidPrgrsOrd": "bid_prgrs_ord",
            "bidPbancPgstCd": "bid_pbanc_pgst_cd",
            "bidPbancPgstCdNm": "bid_pbanc_pgst_cd_nm",
            "sfbrSlctnOrd": "sfbr_slctn_ord",
            "sfbrSlctnRsltCd": "sfbr_slctn_rslt_cd",
            "docSbmsnDdlnDt": "doc_sbmsn_ddln_dt",
            "cvlnQlemCrtrNo": "cvln_qlem_crtr_no",
            "cvlnQlemPgstCd": "cvln_qlem_pgst_cd",
            "objtdmdTermDt": "objtdmd_term_dt",
            "bdngAmtYnNm": "bdng_amt_yn_nm",
            "slprRcptDdlnDt1": "slpr_rcpt_ddln_dt1",
        }
        mapped: dict[str, Any] = {}  # 매핑 결과.
        for key, value in raw.items():  # 원본 순회.
            target = mapping.get(key)  # 매핑 키 확인.
            if target:  # 매핑 대상이면.
                mapped[target] = value  # 변환 저장.
        return mapped  # 변환 결과 반환.

    def _maybe_snapshot_detail(self, item: BidNoticeListItem, body: dict[str, Any]) -> None:  # 상세 스냅샷.
        if not self._snapshot:  # 스냅샷 비활성.
            return  # 종료.
        result = body.get("result", {}) if isinstance(body, dict) else {}  # 응답 안전 처리.
        unexpected = self._find_unexpected_keys(
            result,
            {
                "bidPbancMap",
                "pbancOrgMap",
                "bidPbancItemlist",
                "bidLmtRgnList",
                "bidLmtIntpList",
                "dmLcnsLmtPrmsIntpList",
                "rbidList",
                "bdngCrstList",
                "bidPstmNomnEtpsList",
                "bidInfoList",
                "bidBsneCndtCrtrCdMap",
                "bsamtMap",
            },
        )
        if not unexpected:  # 예상 외 키가 없으면.
            return  # 저장 생략.
        key = f"{item.bid_pbanc_no}_{item.bid_pbanc_ord}"  # 파일 키 구성.
        payload = self._wrap_snapshot_payload(body, unexpected)  # 메타 포함 래핑.
        self._snapshot.save(f"detail_{datetime.now().strftime('%Y%m%d')}", key, payload)  # 스냅샷 저장.
        self._logger.info("snapshot_saved type=detail key=%s unexpected=%s", key, unexpected)  # 저장 로그.

    def _maybe_snapshot_opening(self, item: BidNoticeListItem, body: dict[str, Any]) -> None:  # 개찰 스냅샷.
        if not self._snapshot:  # 스냅샷 비활성.
            return  # 종료.
        result = body.get("result", {}) if isinstance(body, dict) else {}  # 응답 안전 처리.
        unexpected = self._find_unexpected_keys(result, {"pbancMap", "grdLisList", "oobsRsltList"})
        if not unexpected:  # 예상 외 키가 없으면.
            return  # 저장 생략.
        key = f"{item.bid_pbanc_no}_{item.bid_pbanc_ord}"  # 파일 키 구성.
        payload = self._wrap_snapshot_payload(body, unexpected)  # 메타 포함 래핑.
        self._snapshot.save(f"opening_{datetime.now().strftime('%Y%m%d')}", key, payload)  # 스냅샷 저장.
        self._logger.info("snapshot_saved type=opening key=%s unexpected=%s", key, unexpected)  # 저장 로그.

    def _find_unexpected_keys(self, result: dict[str, Any], expected: set[str]) -> list[str]:  # 예상 외 키 탐지.
        if not isinstance(result, dict):  # 타입 방어.
            return []  # 비교 불가.
        unexpected = [key for key in result.keys() if key not in expected]  # 예상 외 키 수집.
        return sorted(unexpected)  # 정렬 반환.

    def _wrap_snapshot_payload(self, body: dict[str, Any], unexpected: list[str]) -> dict[str, Any]:  # 스냅샷 래핑.
        return {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "unexpected_keys": unexpected,
            },
            "body": body,
        }

    def _maybe_snapshot_list(self, page_index: int, body: dict[str, Any]) -> None:  # 목록 스냅샷.
        if not self._snapshot:  # 스냅샷 비활성.
            return  # 종료.
        if self._config.snapshot_mode != "all":  # 전체 저장 모드가 아니면.
            return  # 저장 생략.
        key = f"page_{page_index}"  # 파일 키 구성.
        payload = self._wrap_snapshot_payload(body, [])  # 메타 포함 래핑.
        self._snapshot.save(f"list_{datetime.now().strftime('%Y%m%d')}", key, payload)  # 스냅샷 저장.
        self._logger.info("snapshot_saved type=list key=%s mode=%s", key, self._config.snapshot_mode)

    def _build_detail_from_list(  # 상세 기본값 생성.
        self,
        item: BidNoticeListItem,  # 목록 아이템.
        detail_raw: dict[str, Any],  # 상세 원본 맵.
    ) -> BidNoticeDetail:
        mapping = {  # 상세 응답 필드 매핑.
            "bidPbancNo": "bid_pbanc_no",
            "bidPbancOrd": "bid_pbanc_ord",
            "bidClsfNo": "bid_clsf_no",
            "bidPrgrsOrd": "bid_prgrs_ord",
            "bidPbancNm": "bid_pbanc_nm",
            "bidPbancNum": "bid_pbanc_num",
            "pbancSttsCd": "pbanc_stts_cd",
            "pbancSttsCdNm": "pbanc_stts_cd_nm",
            "prcmBsneSeCd": "prcm_bsne_se_cd",
            "prcmBsneSeCdNm": "prcm_bsne_se_cd_nm",
            "bidMthdCd": "bid_mthd_cd",
            "bidMthdCdNm": "bid_mthd_cd_nm",
            "stdCtrtMthdCd": "std_ctrt_mthd_cd",
            "stdCtrtMthdCdNm": "std_ctrt_mthd_cd_nm",
            "scsbdMthdCd": "scsbd_mthd_cd",
            "scsbdMthdCdNm": "scsbd_mthd_cd_nm",
            "pbancInstUntyGrpNo": "pbanc_inst_unty_grp_no",
            "pbancInstUntyGrpNoNm": "pbanc_inst_unty_grp_no_nm",
            "grpNm": "grp_nm",
            "picId": "pic_id",
            "picIdNm": "pic_id_nm",
            "bidBlffId": "bid_blff_id",
            "bidBlffIdNm": "bid_blff_id_nm",
            "bsneTlphNo": "bsne_tlph_no",
            "bsneFaxNo": "bsne_fax_no",
            "bsneEml": "bsne_eml",
            "pbancPstgDt": "pbanc_pstg_dt",
            "slprRcptBgngDt": "slpr_rcpt_bgng_dt",
            "slprRcptDdlnDt": "slpr_rcpt_ddln_dt",
            "onbsPrnmntDt": "onbs_prnmnt_dt",
            "bidQlfcRegDt": "bid_qlfc_reg_dt",
            "onbsPlacNm": "onbs_plac_nm",
            "zip": "zip",
            "baseAddr": "base_addr",
            "dtlAddr": "dtl_addr",
            "untyAddr": "unty_addr",
            "edocNo": "edoc_no",
            "usrDocNoVal": "usr_doc_no_val",
            "rbidPrmsYn": "rbid_prms_yn",
            "pbancPstgYn": "pbanc_pstg_yn",
            "rgnLmtYn": "rgn_lmt_yn",
            "lcnsLmtYn": "lcns_lmt_yn",
            "pnprUseYn": "pnpr_use_yn",
            "pnprRlsYn": "pnpr_rls_yn",
            "untyAtchFileNo": "unty_atch_file_no",
        }
        mapped = self._map_detail_row(detail_raw, mapping)  # 상세 매핑.
        fallback = {  # 목록 기반 필수값 보정.
            "bid_pbanc_no": item.bid_pbanc_no,
            "bid_pbanc_ord": item.bid_pbanc_ord,
            "bid_clsf_no": item.bid_clsf_no,
            "bid_prgrs_ord": item.bid_prgrs_ord,
            "bid_pbanc_nm": item.bid_pbanc_nm,
            "bid_pbanc_num": item.bid_pbanc_num,
            "pbanc_stts_cd": item.pbanc_stts_cd,
            "pbanc_stts_cd_nm": item.pbanc_stts_cd_nm,
        }
        merged = {**fallback, **mapped}  # 상세 우선값 병합.
        return BidNoticeDetail(**merged)  # 상세 모델 생성.

    def _map_detail_row(  # 상세 필드 매핑.
        self,
        raw: dict[str, Any],  # 원본 맵.
        mapping: dict[str, str],  # 매핑 규칙.
    ) -> dict[str, Any]:
        mapped: dict[str, Any] = {}  # 매핑 결과.
        for key, value in raw.items():  # 원본 순회.
            target = mapping.get(key)  # 매핑 키 확인.
            if target:  # 매핑 대상이면.
                mapped[target] = value  # 변환 저장.
        return mapped  # 변환 결과 반환.
