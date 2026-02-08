from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import logging  # 로깅.
from typing import Any, Optional  # 범용 타입과 선택적 타입.

from src.core.config import CrawlConfig  # 크롤링 설정 모델.
from src.domain.models import BidNoticeDetail, BidNoticeListItem  # 도메인 모델.
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
        self._logger = logging.getLogger("service")  # 로거 생성.

    def run(self, page: Any, max_pages: Optional[int]) -> None:  # 실행 진입점
        target_pages = self._config.max_pages  # 기본 페이지 수.
        if max_pages is not None:  # CLI 제한이 있으면.
            target_pages = min(target_pages, max_pages)  # 매걔변수와 시스템 설정중 더 작은 값 사용.
        self._logger.info("crawl_start pages=%s", target_pages)  # 시작 로그.
        page.goto(self._config.list_url, wait_until="networkidle")  # 목록 페이지 이동.
        page.wait_for_selector(self._config.selectors.list_row)  # 목록 로드 대기.
        for page_index in range(target_pages):  # 페이지 반복.
            raw_rows = self._parser.parse_list(page)  # 목록 파싱.
            items: list[BidNoticeListItem] = []  # 변환된 모델 리스트.
            detail_items: list[BidNoticeDetail] = []  # 상세 모델 리스트.
            for row_index, raw in enumerate(raw_rows):  # 각 행 변환.
                mapped = self._map_list_row(raw)  # 필드 매핑.
                try:  # 검증 실패를 대비.
                    list_item = BidNoticeListItem(**mapped)  # 모델 생성.
                    items.append(list_item)  # 목록 추가.
                except Exception as exc:  # 검증 실패.
                    self._logger.warning("list_row_skip err=%s raw=%s", exc, raw)  # 스킵 로그.
                    continue  # 다음 행.
                if self._config.selectors.detail_popup and self._config.selectors.detail_close:  # 상세 설정 확인.
                    self._open_detail(page, row_index)  # 상세 팝업 오픈.
                    self._parser.parse_detail(page)  # 상세 파싱(미확정 필드 대비).
                    self._close_detail(page)  # 상세 팝업 닫기.
                detail_items.append(self._build_detail_from_list(list_item))  # 최소 상세 저장.
            if items:  # 저장할 항목이 있으면.
                self._repo.save_list_items(items)  # 목록 저장.
            if detail_items:  # 상세 항목이 있으면.
                self._repo.save_detail_items(detail_items)  # 상세 저장.
            if page_index + 1 >= target_pages:  # 마지막 페이지면 종료.
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
        self._logger.info("crawl_done")  # 종료 로그.

    def _open_detail(self, page: Any, index: int) -> None:  # 상세 팝업 열기.
        link = page.locator(self._config.selectors.list_link).nth(index)  # 해당 행 링크.
        link.click()  # 상세 클릭.
        page.wait_for_selector(self._config.selectors.detail_popup)  # 팝업 로드 대기.

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

    def _build_detail_from_list(self, item: BidNoticeListItem) -> BidNoticeDetail:  # 상세 기본값 생성.
        return BidNoticeDetail(  # 목록 기반으로 필수 필드만 채운다.
            bid_pbanc_no=item.bid_pbanc_no,
            bid_pbanc_ord=item.bid_pbanc_ord,
            bid_clsf_no=item.bid_clsf_no,
            bid_prgrs_ord=item.bid_prgrs_ord,
            bid_pbanc_nm=item.bid_pbanc_nm,
            bid_pbanc_num=item.bid_pbanc_num,
            pbanc_stts_cd=item.pbanc_stts_cd,
            pbanc_stts_cd_nm=item.pbanc_stts_cd_nm,
        )
