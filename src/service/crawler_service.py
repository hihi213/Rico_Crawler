from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import json  # JSON 직렬화.
import logging  # 로깅.
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
                items = self._build_list_items(raw_rows)  # 목록 모델 생성.
                detail_items: list[BidNoticeDetail] = []  # 상세 모델 리스트.
                opening_summaries: list[BidOpeningSummary] = []  # 개찰 요약 리스트.
                opening_results: list[BidOpeningResult] = []  # 개찰 결과 리스트.
                attachments: list[AttachmentItem] = []  # 첨부 리스트.
                noce_items: list[NoceItem] = []  # 공지 리스트.
                for item in items:  # 상세/부가 데이터 수집.
                    detail_raw = self._fetch_detail_via_api(page, item)  # 상세 API 호출.
                    detail_items.append(self._build_detail_from_list(item, detail_raw))  # 상세 모델 생성.
                    noce_items.extend(self._build_noce_items(page, item))  # 공지 리스트.
                    attachments.extend(self._build_attachment_items(page, detail_raw))  # 첨부 리스트.
                    opening_summary, opening_rows = self._build_opening_items(page, item)  # 개찰 결과.
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
            items = self._build_list_items(raw_rows)  # 목록 모델 생성.
            detail_items: list[BidNoticeDetail] = []  # 상세 모델 리스트.
            for row_index, item in enumerate(items):  # 각 행 변환.
                detail_data: dict[str, Any] = {}  # 상세 원본 맵.
                if self._config.selectors.detail_popup and self._config.selectors.detail_close:  # 상세 설정 확인.
                    detail_data = self._open_detail_and_fetch(page, row_index)  # 상세 응답 확보.
                    self._close_detail(page)  # 상세 팝업 닫기.
                detail_item = self._build_detail_from_list(item, detail_data)  # 상세 생성.
                detail_items.append(detail_item)  # 상세 저장 목록에 추가.
            if items:  # 저장할 항목이 있으면.
                self._repo.save_list_items(items)  # 목록 저장.
            if detail_items:  # 상세 항목이 있으면.
                self._repo.save_detail_items(detail_items)  # 상세 저장.
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
            payload = dict(self._config.list_api_payload)  # 원본 보호.
            payload["currentPage"] = current_page  # 페이지 갱신.
            resp = page.request.post(  # API 호출.
                self._config.list_api_url,
                data=json.dumps({"dlParamM": payload}),
                headers=self._config.list_api_headers,
            )
            body = resp.json()  # JSON 파싱.
            if body.get("ErrorCode") != 0:  # 오류 처리.
                raise RuntimeError(f"list_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            result = body.get("result", [])  # 결과 리스트.
            if not isinstance(result, list):
                raise RuntimeError("list_api_invalid_result")
            return result

        try:
            return _call()
        except Exception as exc:
            self._logger.warning("list_api_skip err=%s page=%s", exc, current_page)
            return []

    def _build_list_items(self, raw_rows: list[dict[str, Any]]) -> list[BidNoticeListItem]:  # 목록 모델 생성.
        items: list[BidNoticeListItem] = []  # 변환된 모델 리스트.
        for raw in raw_rows:  # 각 행 변환.
            mapped = self._map_list_row(raw)  # 필드 매핑.
            try:  # 검증 실패를 대비.
                list_item = BidNoticeListItem(**mapped)  # 모델 생성.
                items.append(list_item)  # 목록 추가.
            except Exception as exc:  # 검증 실패.
                self._logger.warning("list_row_skip err=%s raw=%s", exc, raw)  # 스킵 로그.
                continue  # 다음 행.
        return items

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
            if body.get("ErrorCode") != 0:
                raise RuntimeError(f"detail_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            return self._parser.parse_detail(body)

        try:
            return _call()
        except Exception as exc:
            self._logger.warning("detail_api_skip err=%s key=%s", exc, item.bid_pbanc_no)
            return {}

    def _build_noce_items(self, page: Any, item: BidNoticeListItem) -> list[NoceItem]:  # 공지 항목 생성.
        if not self._config.noce_api_url:
            return []
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
            return []
        results: list[NoceItem] = []
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
        return results

    def _build_attachment_items(self, page: Any, detail_raw: dict[str, Any]) -> list[AttachmentItem]:  # 첨부 항목 생성.
        if not self._config.attachment_api_url:
            return []
        unty_atch_file_no = detail_raw.get("untyAtchFileNo")
        if not unty_atch_file_no:
            return []
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
            return []
        results: list[AttachmentItem] = []
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
        return results

    def _build_opening_items(
        self, page: Any, item: BidNoticeListItem
    ) -> tuple[Optional[BidOpeningSummary], list[BidOpeningResult]]:  # 개찰 항목 생성.
        if not self._config.opening_api_url:
            return None, []
        if not item.bid_clsf_no or not item.bid_prgrs_ord:
            return None, []
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
            if body.get("ErrorCode") != 0:
                raise RuntimeError(f"opening_api_error code={body.get('ErrorCode')} msg={body.get('ErrorMsg')}")
            return self._parser.parse_opening(body)

        try:
            summary_raw, rows_raw = _call()
        except Exception as exc:
            self._logger.warning("opening_api_skip err=%s key=%s", exc, item.bid_pbanc_no)
            return None, []
        summary = None
        if summary_raw:
            mapped = self._map_opening_summary(summary_raw)
            try:
                summary = BidOpeningSummary(**mapped)
            except Exception as exc:
                self._logger.warning("opening_summary_skip err=%s raw=%s", exc, summary_raw)
        results: list[BidOpeningResult] = []
        for row in rows_raw:
            mapped = self._map_opening_result(row)
            try:
                results.append(BidOpeningResult(**mapped))
            except Exception as exc:
                self._logger.warning("opening_row_skip err=%s raw=%s", exc, row)
        return summary, results

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
