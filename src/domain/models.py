from __future__ import annotations  # 타입 힌트에서 전방 참조를 허용한다.

# docs/schema.md 기준으로 파싱/저장을 일관되게 유지하기 위한 도메인 모델.

from datetime import datetime  # 날짜/시간 정규화에 사용.
from typing import Optional  # 선택적 필드 타입 표현.

from pydantic import BaseModel, Field  # 모든 도메인 모델의 기반 클래스와 제약 선언.

try:  # Pydantic v2의 validator를 우선 시도한다.
    from pydantic import field_validator  # v2 전용 validator 데코레이터.

    _USE_PYDANTIC_V2 = True  # v2 사용 여부 플래그.
except ImportError:  # pragma: no cover - pydantic v1 fallback
    from pydantic import validator  # v1 전용 validator 데코레이터.

    _USE_PYDANTIC_V2 = False  # v1 사용 여부 플래그.


def _strip_or_none(value: Optional[str]) -> Optional[str]:  # 공백 제거 후 빈 값 처리.
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    stripped = value.strip()  # 양쪽 공백 제거.
    return stripped if stripped else None  # 빈 문자열이면 None 반환.


def _normalize_doc_no(value: Optional[str]) -> Optional[str]:  # 문서번호 공백 제거.
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    return "".join(value.split())  # 모든 공백을 제거한다.


def _normalize_biz_reg_no(value: Optional[str]) -> Optional[str]:  # 사업자등록번호 하이픈 제거.
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    return value.replace("-", "").strip() or None  # 하이픈 제거 후 빈 값이면 None.


def _parse_bool_yn(value: Optional[str]) -> Optional[bool]:  # Y/N 플래그를 bool로 변환. 중요한 기준이니 대문자로 기준
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    if isinstance(value, bool):  # 이미 bool이면 그대로 사용.
        return value  # 그대로 반환.
    normalized = value.strip().upper()  # 공백 제거 후 대문자화.
    if normalized == "Y":  # Y는 True.
        return True  # True 반환.
    if normalized == "N":  # N은 False.
        return False  # False 반환.
    return None  # 그 외 값은 None 처리.


def _parse_int(value: Optional[str]) -> Optional[int]:  # 금액/숫자 필드 정규화.
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    if isinstance(value, int):  # 이미 int면 그대로 사용.
        return value  # 그대로 반환.
    raw = str(value).replace(",", "").strip()  # 콤마 제거 후 공백 제거.
    if raw == "":  # 빈 문자열이면 None 처리.
        return None  # None 반환.
    return int(raw)  # 숫자로 변환.


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:  # 날짜/시간 문자열 파싱.
    if value is None:  # 값이 없으면 None 유지.
        return None  # None 반환.
    if isinstance(value, datetime):  # 이미 datetime이면 그대로 사용.
        return value  # 그대로 반환.
    raw = str(value).strip()  # 문자열로 변환 후 공백 제거.
    if raw == "":  # 빈 문자열이면 None 처리.
        return None  # None 반환.
    formats = [  # 허용하는 날짜/시간 포맷 목록.
        "%Y/%m/%d %H:%M:%S",  # 초 포함.
        "%Y/%m/%d %H:%M",  # 분까지만.
        "%Y-%m-%d %H:%M:%S",  # 하이픈 구분, 초 포함.
        "%Y-%m-%d %H:%M",  # 하이픈 구분, 분까지만.
        "%Y/%m/%d",  # 날짜만(슬래시).
        "%Y-%m-%d",  # 날짜만(하이픈).
        "%Y%m%d",  # 날짜만(숫자 8자리).
    ]  # 포맷 리스트 종료.
    for fmt in formats:  # 각 포맷을 순회하며 파싱 시도.
        try:  # 파싱 실패를 대비한 try 블록.
            return datetime.strptime(raw, fmt)  # 파싱 성공 시 반환.
        except ValueError:  # 해당 포맷 불일치.
            continue  # 다음 포맷으로 진행.
    raise ValueError(f"Unsupported datetime format for value: {value}")  # 모두 실패 시 에러.


def _before_validator(*fields: str):  # v1/v2 공통 validator 래퍼.
    if _USE_PYDANTIC_V2:  # v2 환경이면.
        return field_validator(*fields, mode="before")  # v2 before validator 반환.
    return validator(*fields, pre=True)  # v1 before validator 반환.


class BidNoticeKey(BaseModel):  # 공통 식별자 모델.
    # 목록/상세/개찰 공통 식별자. 조인 및 재시작(체크포인트) 기준으로 사용.
    bid_pbanc_no: str  # 입찰공고번호.
    bid_pbanc_ord: str  # 차수.
    bid_clsf_no: Optional[str] = None  # 분류 번호(상세/개찰 기준).
    bid_prgrs_ord: Optional[str] = None  # 진행 차수(상세/개찰 기준).


class BidNoticeListItem(BidNoticeKey):  # 목록 공고 모델.
    # 목록 API 응답과 페이징 메타에 맞춘 필수 필드.
    bid_pbanc_nm: str  # 공고명.
    bid_pbanc_num: str  # 공고번호-차수 표시값.
    pbanc_stts_cd: str  # 공고상태 코드.
    pbanc_stts_cd_nm: str  # 공고상태 코드명.
    prcm_bsne_se_cd: str  # 공고분류 코드.
    prcm_bsne_se_cd_nm: str  # 공고분류 코드명.
    bid_mthd_cd: str  # 입찰방식 코드.
    bid_mthd_cd_nm: str  # 입찰방식 코드명.
    std_ctrt_mthd_cd: str  # 계약방법 코드.
    std_ctrt_mthd_cd_nm: str  # 계약방법 코드명.
    scsbd_mthd_cd: str  # 낙찰방법 코드.
    scsbd_mthd_cd_nm: str  # 낙찰방법 코드명.
    grp_nm: str  # 기관명/조합명.
    pbanc_pstg_dt: datetime  # 공고게시일시.
    slpr_rcpt_ddln_dt: Optional[datetime]  # 입찰마감일시.
    pbanc_knd_cd: str  # 공고종류 코드.
    pbanc_knd_cd_nm: str  # 공고종류 코드명.
    pbanc_stts_grid_cd_nm: str  # 진행상태(그리드 표기).
    row_num: int  # 화면 행 번호.
    tot_cnt: int  # 전체 건수.
    current_page: int  # 현재 페이지.
    record_count_per_page: int  # 페이지 크기.
    next_row_yn: Optional[bool]  # 다음 행 존재 여부.
    # 일부 샘플에서만 보이거나 플래그/부가 메타로 쓰이는 선택 필드.
    edoc_no: Optional[str] = None  # 전자문서번호.
    usr_doc_no_val: Optional[str] = None  # 사용자 문서번호.
    pbanc_inst_unty_grp_no: Optional[str] = None  # 기관 식별자.
    pbanc_pstg_yn: Optional[bool] = None  # 게시 여부.
    pbanc_dscr_trgt_yn: Optional[bool] = None  # 공개대상 여부.
    slpr_rcpt_bgng_yn: Optional[bool] = None  # 접수시작 여부.
    slpr_rcpt_ddln_yn: Optional[bool] = None  # 접수마감 여부.
    onbs_prnmnt_yn: Optional[bool] = None  # 개찰 관련 여부.
    bid_qlfc_end_yn: Optional[bool] = None  # 자격 심사 종료 여부.
    pbanc_bfss_yn: Optional[bool] = None  # 사전공고 여부.
    bid_clsf_no: Optional[str] = None  # 분류 번호(목록에 포함되는 경우).
    bid_prgrs_ord: Optional[str] = None  # 진행 차수(목록에 포함되는 경우).
    bid_pbanc_pgst_cd: Optional[str] = None  # 공고게시 코드.
    sfbr_slctn_ord: Optional[str] = None  # 낙찰자선정 차수.
    sfbr_slctn_rslt_cd: Optional[str] = None  # 낙찰자선정 결과 코드.
    doc_sbmsn_ddln_dt: Optional[datetime] = None  # 문서제출 마감일시.
    cvln_qlem_crtr_no: Optional[str] = None  # 적격심사 기준 번호.
    cvln_qlem_pgst_cd: Optional[str] = None  # 적격심사 게시 코드.
    objtdmd_term_dt: Optional[datetime] = None  # 이의신청 기간.
    bdng_amt_yn_nm: Optional[str] = None  # 투찰금액 여부 표시(화면 표기).
    slpr_rcpt_ddln_dt1: Optional[datetime] = None  # 추가 마감일시.

    @_before_validator(  # 날짜/시간 필드 파싱.
        "pbanc_pstg_dt",  # 공고게시일시.
        "slpr_rcpt_ddln_dt",  # 입찰마감일시.
        "doc_sbmsn_ddln_dt",  # 문서제출 마감.
        "objtdmd_term_dt",  # 이의신청 기간.
        "slpr_rcpt_ddln_dt1",  # 추가 마감일시.
    )
    def _parse_list_datetimes(cls, value: Optional[str]) -> Optional[datetime]:  # 목록 일시 파싱.
        return _parse_datetime(value)  # 공통 파서 사용.

    @_before_validator(  # Y/N 플래그 파싱.
        "next_row_yn",  # 다음 행 존재 여부.
        "pbanc_pstg_yn",  # 게시 여부.
        "pbanc_dscr_trgt_yn",  # 공개대상 여부.
        "slpr_rcpt_bgng_yn",  # 접수시작 여부.
        "slpr_rcpt_ddln_yn",  # 접수마감 여부.
        "onbs_prnmnt_yn",  # 개찰 관련 여부.
        "bid_qlfc_end_yn",  # 자격 심사 종료 여부.
        "pbanc_bfss_yn",  # 사전공고 여부.
    )
    def _parse_list_flags(cls, value: Optional[str]) -> Optional[bool]:  # 목록 플래그 파싱.
        return _parse_bool_yn(value)  # 공통 파서 사용.

    @_before_validator("edoc_no", "usr_doc_no_val")  # 문서번호 정규화.
    def _normalize_list_doc_no(cls, value: Optional[str]) -> Optional[str]:  # 목록 문서번호 정리.
        return _normalize_doc_no(_strip_or_none(value))  # 공백 제거 후 정규화.


class BidNoticeDetail(BidNoticeKey):  # 상세 공고 모델.
    # 상세 식별 및 라벨링에 필요한 필수 필드.
    bid_pbanc_nm: str  # 공고명.
    bid_pbanc_num: str  # 공고번호-차수 표시값.
    pbanc_stts_cd: str  # 공고상태 코드.
    pbanc_stts_cd_nm: str  # 공고상태 코드명.
    # 공고 유형/상세 API 제공 여부에 따라 달라지는 선택 필드.
    prcm_bsne_se_cd: Optional[str] = None  # 공고분류 코드.
    prcm_bsne_se_cd_nm: Optional[str] = None  # 공고분류 코드명.
    bid_mthd_cd: Optional[str] = None  # 입찰방식 코드.
    bid_mthd_cd_nm: Optional[str] = None  # 입찰방식 코드명.
    std_ctrt_mthd_cd: Optional[str] = None  # 계약방법 코드.
    std_ctrt_mthd_cd_nm: Optional[str] = None  # 계약방법 코드명.
    scsbd_mthd_cd: Optional[str] = None  # 낙찰방법 코드.
    scsbd_mthd_cd_nm: Optional[str] = None  # 낙찰방법 코드명.
    pbanc_inst_unty_grp_no: Optional[str] = None  # 기관 식별자.
    pbanc_inst_unty_grp_no_nm: Optional[str] = None  # 기관 식별자명.
    grp_nm: Optional[str] = None  # 기관/조합명.
    pic_id: Optional[str] = None  # 담당자 ID.
    pic_id_nm: Optional[str] = None  # 담당자명.
    bid_blff_id: Optional[str] = None  # 집행관 ID.
    bid_blff_id_nm: Optional[str] = None  # 집행관명.
    bsne_tlph_no: Optional[str] = None  # 연락처.
    bsne_fax_no: Optional[str] = None  # 팩스.
    bsne_eml: Optional[str] = None  # 이메일.
    pbanc_pstg_dt: Optional[datetime] = None  # 공고게시일시.
    slpr_rcpt_bgng_dt: Optional[datetime] = None  # 접수시작일시.
    slpr_rcpt_ddln_dt: Optional[datetime] = None  # 접수마감일시.
    onbs_prnmnt_dt: Optional[datetime] = None  # 개찰예정일시.
    bid_qlfc_reg_dt: Optional[datetime] = None  # 자격심사 등록일.
    onbs_plac_nm: Optional[str] = None  # 개찰장소.
    zip: Optional[str] = None  # 우편번호.
    base_addr: Optional[str] = None  # 기본 주소.
    dtl_addr: Optional[str] = None  # 상세 주소.
    unty_addr: Optional[str] = None  # 통합 주소.
    edoc_no: Optional[str] = None  # 전자문서번호.
    usr_doc_no_val: Optional[str] = None  # 사용자 문서번호.
    rbid_prms_yn: Optional[bool] = None  # 재입찰 허용 여부.
    pbanc_pstg_yn: Optional[bool] = None  # 게시 여부.
    rgn_lmt_yn: Optional[bool] = None  # 지역 제한 여부.
    lcns_lmt_yn: Optional[bool] = None  # 면허 제한 여부.
    pnpr_use_yn: Optional[bool] = None  # 제안서 사용 여부.
    pnpr_rls_yn: Optional[bool] = None  # 제안서 공개 여부.
    unty_atch_file_no: Optional[str] = None  # 첨부파일 그룹 키.

    @_before_validator(  # 상세 일시 파싱.
        "pbanc_pstg_dt",  # 공고게시일시.
        "slpr_rcpt_bgng_dt",  # 접수시작일시.
        "slpr_rcpt_ddln_dt",  # 접수마감일시.
        "onbs_prnmnt_dt",  # 개찰예정일시.
        "bid_qlfc_reg_dt",  # 자격심사 등록일.
    )
    def _parse_detail_datetimes(cls, value: Optional[str]) -> Optional[datetime]:  # 상세 일시 파싱.
        return _parse_datetime(value)  # 공통 파서 사용.

    @_before_validator(  # 상세 플래그 파싱.
        "rbid_prms_yn",  # 재입찰 허용 여부.
        "pbanc_pstg_yn",  # 게시 여부.
        "rgn_lmt_yn",  # 지역 제한 여부.
        "lcns_lmt_yn",  # 면허 제한 여부.
        "pnpr_use_yn",  # 제안서 사용 여부.
        "pnpr_rls_yn",  # 제안서 공개 여부.
    )
    def _parse_detail_flags(cls, value: Optional[str]) -> Optional[bool]:  # 상세 플래그 파싱.
        return _parse_bool_yn(value)  # 공통 파서 사용.

    @_before_validator("edoc_no", "usr_doc_no_val")  # 문서번호 정규화.
    def _normalize_detail_doc_no(cls, value: Optional[str]) -> Optional[str]:  # 상세 문서번호 정리.
        return _normalize_doc_no(_strip_or_none(value))  # 공백 제거 후 정규화.


class BidOpeningSummary(BidNoticeKey):  # 개찰결과 요약 모델.
    # 개찰결과 API의 요약 맵(pbancMap). 목록 결과와 분리 유지.
    bid_pbanc_nm: str  # 공고명.
    bid_pbanc_num: str  # 공고번호-차수 표시값.
    pbanc_stts_cd: str  # 공고상태 코드.
    pbanc_stts_cd_nm: str  # 공고상태 코드명.
    # API 응답에 따라 존재하는 선택 요약 필드.
    prcm_bsne_se_cd: Optional[str] = None  # 공고분류 코드.
    prcm_bsne_se_cd_nm: Optional[str] = None  # 공고분류 코드명.
    bid_mthd_cd: Optional[str] = None  # 입찰방식 코드.
    bid_mthd_cd_nm: Optional[str] = None  # 입찰방식 코드명.
    std_ctrt_mthd_cd: Optional[str] = None  # 계약방법 코드.
    std_ctrt_mthd_cd_nm: Optional[str] = None  # 계약방법 코드명.
    scsbd_mthd_cd: Optional[str] = None  # 낙찰방법 코드.
    scsbd_mthd_cd_nm: Optional[str] = None  # 낙찰방법 코드명.
    pbanc_inst_unty_grp_no: Optional[str] = None  # 기관 식별자.
    pbanc_inst_unty_grp_no_nm: Optional[str] = None  # 기관 식별자명.
    grp_nm: Optional[str] = None  # 기관/조합명.
    bid_blff_id: Optional[str] = None  # 집행관 ID.
    bid_blff_id_nm: Optional[str] = None  # 집행관명.
    ibx_onbs_prnmnt_dt: Optional[datetime] = None  # 개찰예정일시.
    ibx_onbs_dt: Optional[datetime] = None  # 실제 개찰일시.
    edoc_no: Optional[str] = None  # 전자문서번호.
    usr_doc_no_val: Optional[str] = None  # 사용자 문서번호.

    @_before_validator("ibx_onbs_prnmnt_dt", "ibx_onbs_dt")  # 개찰 일시 파싱.
    def _parse_opening_summary_datetimes(  # 개찰 요약 일시 파싱.
        cls, value: Optional[str]  # 원본 값.
    ) -> Optional[datetime]:  # 결과 타입.
        return _parse_datetime(value)  # 공통 파서 사용.

    @_before_validator("edoc_no", "usr_doc_no_val")  # 문서번호 정규화.
    def _normalize_summary_doc_no(cls, value: Optional[str]) -> Optional[str]:  # 요약 문서번호 정리.
        return _normalize_doc_no(_strip_or_none(value))  # 공백 제거 후 정규화.


class BidOpeningResult(BidNoticeKey):  # 개찰결과 목록 모델.
    # 개찰결과 목록(oobsRsltList) 단위의 결과/평가 정보.
    ibx_onbs_rnkg: int  # 순위.
    ibx_grp_nm: str  # 업체명.
    ibx_bdng_amt: int = Field(ge=0)  # 투찰금액(음수 불가).
    ibx_slpr_rcptn_dt: datetime  # 투찰일시.
    # 공고/상태에 따라 누락될 수 있는 선택 필드.
    ibx_bzmn_reg_no: Optional[str] = None  # 사업자등록번호.
    ibx_rprsv_nm: Optional[str] = None  # 대표자명.
    bidr_prsn_no: Optional[str] = None  # 입찰자 번호.
    bidr_prsn_nm: Optional[str] = None  # 입찰자명.
    bid_ufns_rsn_cd: Optional[str] = None  # 사전판정 코드.
    bid_ufns_rsn_nm: Optional[str] = None  # 사전판정 코드명.
    ufns_yn: Optional[bool] = None  # 사전판정 여부.
    ibx_evl_scr_prpl: Optional[str] = None  # 제안서 평가점수.
    ibx_evl_scr_prce: Optional[str] = None  # 가격 평가점수.
    ibx_evl_scr_ovrl: Optional[str] = None  # 총점.
    sfbr_slctn_ord: Optional[str] = None  # 낙찰자선정 차수.
    sfbr_slctn_rslt_cd: Optional[str] = None  # 낙찰자선정 결과 코드.

    @_before_validator("ibx_bdng_amt")  # 금액 파싱.
    def _parse_opening_amount(cls, value: Optional[str]) -> Optional[int]:  # 개찰 금액 파싱.
        parsed = _parse_int(value)  # 금액 정규화.
        if parsed is None:  # 필수 값 누락.
            raise ValueError(f"ibx_bdng_amt is required (value={value})")  # 필수값 에러.
        return parsed  # 파싱 결과 반환.

    @_before_validator("ibx_slpr_rcptn_dt")  # 투찰일시 파싱.
    def _parse_opening_datetime(cls, value: Optional[str]) -> Optional[datetime]:  # 개찰 일시 파싱.
        return _parse_datetime(value)  # 공통 파서 사용.

    @_before_validator("ibx_bzmn_reg_no")  # 사업자등록번호 정규화.
    def _normalize_biz_reg_no(cls, value: Optional[str]) -> Optional[str]:  # 사업자번호 정리.
        return _normalize_biz_reg_no(_strip_or_none(value))  # 하이픈 제거.

    @_before_validator("ufns_yn")  # 사전판정 여부 파싱.
    def _parse_opening_flag(cls, value: Optional[str]) -> Optional[bool]:  # 사전판정 플래그.
        return _parse_bool_yn(value)  # 공통 파서 사용.

    @_before_validator("ibx_evl_scr_prpl", "ibx_evl_scr_prce", "ibx_evl_scr_ovrl")  # 점수 정규화.
    def _normalize_eval_scores(cls, value: Optional[str]) -> Optional[str]:  # 점수 문자열화.
        if value is None:
            return None
        return str(value).strip() or None


class AttachmentItem(BaseModel):  # 첨부 메타 모델.
    # 상세/공지 API의 unty_atch_file_no로 연결되는 첨부 메타.
    unty_atch_file_no: str  # 첨부파일 그룹 키.
    atch_file_sqno: int  # 첨부파일 순번.
    bsne_clsf_cd: str  # 업무분류 코드.
    # 파일 유형/저장소 상황에 따라 달라지는 선택 필드.
    atch_file_knd_cd: Optional[str] = None  # 첨부파일 종류 코드.
    atch_file_nm: str  # 저장 파일명.
    orgnl_atch_file_nm: str  # 원본 파일명.
    file_extn_nm: str  # 확장자.
    file_sz: int  # 파일 크기.
    encr_bef_file_sz: Optional[int] = None  # 암호화 전 크기.
    img_url: Optional[str] = None  # 이미지 URL.
    atch_file_dscr: Optional[str] = None  # 첨부 설명.
    mcsc_chck_id_val: Optional[str] = None  # 검사 ID.
    dwnld_prms_yn: Optional[bool] = None  # 다운로드 허용 여부.
    kbrdr_id: Optional[str] = None  # 등록자 ID.
    kbrdr_nm: Optional[str] = None  # 등록자명.
    inpt_dt: Optional[datetime] = None  # 등록일시.
    atch_file_path_nm: Optional[str] = None  # 저장 경로.
    tbl_nm: Optional[str] = None  # 테이블명.
    col_nm: Optional[str] = None  # 컬럼명.
    atch_file_rmrk_cn: Optional[str] = None  # 비고.

    @_before_validator("file_sz", "encr_bef_file_sz")  # 파일 크기 파싱.
    def _parse_file_sizes(cls, value: Optional[str]) -> Optional[int]:  # 파일 크기 정규화.
        return _parse_int(value)  # 공통 파서 사용.

    @_before_validator("inpt_dt")  # 등록일시 파싱.
    def _parse_inpt_dt(cls, value: Optional[str]) -> Optional[datetime]:  # 첨부 등록일 파싱.
        return _parse_datetime(value)  # 공통 파서 사용.

    @_before_validator("dwnld_prms_yn")  # 다운로드 허용 여부 파싱.
    def _parse_download_flag(cls, value: Optional[str]) -> Optional[bool]:  # 다운로드 플래그.
        return _parse_bool_yn(value)  # 공통 파서 사용.


class NoceItem(BaseModel):  # 공지/변경 공고 상세 모델.
    pst_no: str  # 게시 번호.
    bbs_no: str  # 게시판/공고 번호.
    pst_nm: str  # 게시 제목.
    unty_atch_file_no: Optional[str] = None  # 첨부파일 그룹 키.
    use_yn: Optional[bool] = None  # 사용 여부.
    inpt_dt: Optional[datetime] = None  # 등록일시.
    odn3_col_cn: Optional[str] = None  # 기타 컬럼.
    bulk_pst_cn: Optional[str] = None  # 본문/내용.

    @_before_validator("use_yn")  # 사용 여부 파싱.
    def _parse_use_yn(cls, value: Optional[str]) -> Optional[bool]:  # 사용 여부 정규화.
        return _parse_bool_yn(value)  # 공통 파서 사용.

    @_before_validator("inpt_dt")  # 등록일시 파싱.
    def _parse_inpt_dt(cls, value: Optional[str]) -> Optional[datetime]:  # 공지 일시 파싱.
        return _parse_datetime(value)  # 공통 파서 사용.


class CommCd(BaseModel):  # 코드 사전 모델.
    # UI 라벨/필터 매핑을 위한 코드 사전 한 행.
    code_group: str  # 코드 그룹.
    code: str  # 코드.
    code_nm: str  # 코드명.
    use_yn: bool  # 사용 여부.

    @_before_validator("use_yn")  # 사용 여부 파싱.
    def _parse_use_yn(cls, value: Optional[str]) -> Optional[bool]:  # 사용 여부 정규화.
        parsed = _parse_bool_yn(value)  # Y/N 변환.
        if parsed is None:  # 필수값 누락.
            raise ValueError(f"use_yn is required (value={value})")  # 필수값 에러.
        return parsed  # 변환 결과 반환.
