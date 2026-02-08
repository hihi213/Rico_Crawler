from __future__ import annotations

# docs/schema.md 기준으로 파싱/저장을 일관되게 유지하기 위한 도메인 모델.

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

try:
    from pydantic import field_validator

    _USE_PYDANTIC_V2 = True
except ImportError:  # pragma: no cover - pydantic v1 fallback
    from pydantic import validator

    _USE_PYDANTIC_V2 = False


def _strip_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _normalize_doc_no(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return "".join(value.split())


def _normalize_biz_reg_no(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.replace("-", "").strip() or None


def _parse_bool_yn(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = value.strip().upper()
    if normalized == "Y":
        return True
    if normalized == "N":
        return False
    return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raw = str(value).replace(",", "").strip()
    if raw == "":
        return None
    return int(raw)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if raw == "":
        return None
    formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported datetime format: {value}")


def _before_validator(*fields: str):
    if _USE_PYDANTIC_V2:
        return field_validator(*fields, mode="before")
    return validator(*fields, pre=True)


class BidNoticeKey(BaseModel):
    # 목록/상세/개찰 공통 식별자. 조인 및 재시작(체크포인트) 기준으로 사용.
    bid_pbanc_no: str
    bid_pbanc_ord: str
    bid_clsf_no: Optional[str] = None
    bid_prgrs_ord: Optional[str] = None


class BidNoticeListItem(BidNoticeKey):
    # 목록 API 응답과 페이징 메타에 맞춘 필수 필드.
    bid_pbanc_nm: str
    bid_pbanc_num: str
    pbanc_stts_cd: str
    pbanc_stts_cd_nm: str
    prcm_bsne_se_cd: str
    prcm_bsne_se_cd_nm: str
    bid_mthd_cd: str
    bid_mthd_cd_nm: str
    std_ctrt_mthd_cd: str
    std_ctrt_mthd_cd_nm: str
    scsbd_mthd_cd: str
    scsbd_mthd_cd_nm: str
    grp_nm: str
    pbanc_pstg_dt: datetime
    slpr_rcpt_ddln_dt: datetime
    pbanc_knd_cd: str
    pbanc_knd_cd_nm: str
    pbanc_stts_grid_cd_nm: str
    row_num: int
    tot_cnt: int
    current_page: int
    record_count_per_page: int
    next_row_yn: Optional[bool]
    # 일부 샘플에서만 보이거나 플래그/부가 메타로 쓰이는 선택 필드.
    edoc_no: Optional[str] = None
    usr_doc_no_val: Optional[str] = None
    pbanc_inst_unty_grp_no: Optional[str] = None
    pbanc_pstg_yn: Optional[bool] = None
    pbanc_dscr_trgt_yn: Optional[bool] = None
    slpr_rcpt_bgng_yn: Optional[bool] = None
    slpr_rcpt_ddln_yn: Optional[bool] = None
    onbs_prnmnt_yn: Optional[bool] = None
    bid_qlfc_end_yn: Optional[bool] = None
    pbanc_bfss_yn: Optional[bool] = None
    bid_clsf_no: Optional[str] = None
    bid_prgrs_ord: Optional[str] = None
    bid_pbanc_pgst_cd: Optional[str] = None
    sfbr_slctn_ord: Optional[str] = None
    sfbr_slctn_rslt_cd: Optional[str] = None
    doc_sbmsn_ddln_dt: Optional[datetime] = None
    cvln_qlem_crtr_no: Optional[str] = None
    cvln_qlem_pgst_cd: Optional[str] = None
    objtdmd_term_dt: Optional[datetime] = None
    bdng_amt_yn_nm: Optional[str] = None
    slpr_rcpt_ddln_dt1: Optional[datetime] = None

    @_before_validator(
        "pbanc_pstg_dt",
        "slpr_rcpt_ddln_dt",
        "doc_sbmsn_ddln_dt",
        "objtdmd_term_dt",
        "slpr_rcpt_ddln_dt1",
    )
    def _parse_list_datetimes(cls, value: Optional[str]) -> Optional[datetime]:
        return _parse_datetime(value)

    @_before_validator(
        "next_row_yn",
        "pbanc_pstg_yn",
        "pbanc_dscr_trgt_yn",
        "slpr_rcpt_bgng_yn",
        "slpr_rcpt_ddln_yn",
        "onbs_prnmnt_yn",
        "bid_qlfc_end_yn",
        "pbanc_bfss_yn",
    )
    def _parse_list_flags(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_bool_yn(value)

    @_before_validator("edoc_no", "usr_doc_no_val")
    def _normalize_list_doc_no(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_doc_no(_strip_or_none(value))


class BidNoticeDetail(BidNoticeKey):
    # 상세 식별 및 라벨링에 필요한 필수 필드.
    bid_pbanc_nm: str
    bid_pbanc_num: str
    pbanc_stts_cd: str
    pbanc_stts_cd_nm: str
    # 공고 유형/상세 API 제공 여부에 따라 달라지는 선택 필드.
    prcm_bsne_se_cd: Optional[str] = None
    prcm_bsne_se_cd_nm: Optional[str] = None
    bid_mthd_cd: Optional[str] = None
    bid_mthd_cd_nm: Optional[str] = None
    std_ctrt_mthd_cd: Optional[str] = None
    std_ctrt_mthd_cd_nm: Optional[str] = None
    scsbd_mthd_cd: Optional[str] = None
    scsbd_mthd_cd_nm: Optional[str] = None
    pbanc_inst_unty_grp_no: Optional[str] = None
    pbanc_inst_unty_grp_no_nm: Optional[str] = None
    grp_nm: Optional[str] = None
    pic_id: Optional[str] = None
    pic_id_nm: Optional[str] = None
    bid_blff_id: Optional[str] = None
    bid_blff_id_nm: Optional[str] = None
    bsne_tlph_no: Optional[str] = None
    bsne_fax_no: Optional[str] = None
    bsne_eml: Optional[str] = None
    pbanc_pstg_dt: Optional[datetime] = None
    slpr_rcpt_bgng_dt: Optional[datetime] = None
    slpr_rcpt_ddln_dt: Optional[datetime] = None
    onbs_prnmnt_dt: Optional[datetime] = None
    bid_qlfc_reg_dt: Optional[datetime] = None
    onbs_plac_nm: Optional[str] = None
    zip: Optional[str] = None
    base_addr: Optional[str] = None
    dtl_addr: Optional[str] = None
    unty_addr: Optional[str] = None
    edoc_no: Optional[str] = None
    usr_doc_no_val: Optional[str] = None
    rbid_prms_yn: Optional[bool] = None
    pbanc_pstg_yn: Optional[bool] = None
    rgn_lmt_yn: Optional[bool] = None
    lcns_lmt_yn: Optional[bool] = None
    pnpr_use_yn: Optional[bool] = None
    pnpr_rls_yn: Optional[bool] = None
    unty_atch_file_no: Optional[str] = None

    @_before_validator(
        "pbanc_pstg_dt",
        "slpr_rcpt_bgng_dt",
        "slpr_rcpt_ddln_dt",
        "onbs_prnmnt_dt",
        "bid_qlfc_reg_dt",
    )
    def _parse_detail_datetimes(cls, value: Optional[str]) -> Optional[datetime]:
        return _parse_datetime(value)

    @_before_validator(
        "rbid_prms_yn",
        "pbanc_pstg_yn",
        "rgn_lmt_yn",
        "lcns_lmt_yn",
        "pnpr_use_yn",
        "pnpr_rls_yn",
    )
    def _parse_detail_flags(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_bool_yn(value)

    @_before_validator("edoc_no", "usr_doc_no_val")
    def _normalize_detail_doc_no(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_doc_no(_strip_or_none(value))


class BidOpeningSummary(BidNoticeKey):
    # 개찰결과 API의 요약 맵(pbancMap). 목록 결과와 분리 유지.
    bid_pbanc_nm: str
    bid_pbanc_num: str
    pbanc_stts_cd: str
    pbanc_stts_cd_nm: str
    # API 응답에 따라 존재하는 선택 요약 필드.
    prcm_bsne_se_cd: Optional[str] = None
    prcm_bsne_se_cd_nm: Optional[str] = None
    bid_mthd_cd: Optional[str] = None
    bid_mthd_cd_nm: Optional[str] = None
    std_ctrt_mthd_cd: Optional[str] = None
    std_ctrt_mthd_cd_nm: Optional[str] = None
    scsbd_mthd_cd: Optional[str] = None
    scsbd_mthd_cd_nm: Optional[str] = None
    pbanc_inst_unty_grp_no: Optional[str] = None
    pbanc_inst_unty_grp_no_nm: Optional[str] = None
    grp_nm: Optional[str] = None
    bid_blff_id: Optional[str] = None
    bid_blff_id_nm: Optional[str] = None
    ibx_onbs_prnmnt_dt: Optional[datetime] = None
    ibx_onbs_dt: Optional[datetime] = None
    edoc_no: Optional[str] = None
    usr_doc_no_val: Optional[str] = None

    @_before_validator("ibx_onbs_prnmnt_dt", "ibx_onbs_dt")
    def _parse_opening_summary_datetimes(
        cls, value: Optional[str]
    ) -> Optional[datetime]:
        return _parse_datetime(value)

    @_before_validator("edoc_no", "usr_doc_no_val")
    def _normalize_summary_doc_no(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_doc_no(_strip_or_none(value))


class BidOpeningResult(BidNoticeKey):
    # 개찰결과 목록(oobsRsltList) 단위의 결과/평가 정보.
    ibx_onbs_rnkg: int
    ibx_grp_nm: str
    ibx_bdng_amt: int
    ibx_slpr_rcptn_dt: datetime
    # 공고/상태에 따라 누락될 수 있는 선택 필드.
    ibx_bzmn_reg_no: Optional[str] = None
    ibx_rprsv_nm: Optional[str] = None
    bidr_prsn_no: Optional[str] = None
    bidr_prsn_nm: Optional[str] = None
    bid_ufns_rsn_cd: Optional[str] = None
    bid_ufns_rsn_nm: Optional[str] = None
    ufns_yn: Optional[bool] = None
    ibx_evl_scr_prpl: Optional[str] = None
    ibx_evl_scr_prce: Optional[str] = None
    ibx_evl_scr_ovrl: Optional[str] = None
    sfbr_slctn_ord: Optional[str] = None
    sfbr_slctn_rslt_cd: Optional[str] = None

    @_before_validator("ibx_bdng_amt")
    def _parse_opening_amount(cls, value: Optional[str]) -> Optional[int]:
        parsed = _parse_int(value)
        if parsed is None:
            raise ValueError("ibx_bdng_amt is required")
        return parsed

    @_before_validator("ibx_slpr_rcptn_dt")
    def _parse_opening_datetime(cls, value: Optional[str]) -> Optional[datetime]:
        return _parse_datetime(value)

    @_before_validator("ibx_bzmn_reg_no")
    def _normalize_biz_reg_no(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_biz_reg_no(_strip_or_none(value))

    @_before_validator("ufns_yn")
    def _parse_opening_flag(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_bool_yn(value)


class AttachmentItem(BaseModel):
    # 상세/공지 API의 unty_atch_file_no로 연결되는 첨부 메타.
    unty_atch_file_no: str
    atch_file_sqno: int
    bsne_clsf_cd: str
    # 파일 유형/저장소 상황에 따라 달라지는 선택 필드.
    atch_file_knd_cd: Optional[str] = None
    atch_file_nm: str
    orgnl_atch_file_nm: str
    file_extn_nm: str
    file_sz: int
    encr_bef_file_sz: Optional[int] = None
    img_url: Optional[str] = None
    atch_file_dscr: Optional[str] = None
    mcsc_chck_id_val: Optional[str] = None
    dwnld_prms_yn: Optional[bool] = None
    kbrdr_id: Optional[str] = None
    kbrdr_nm: Optional[str] = None
    inpt_dt: Optional[datetime] = None
    atch_file_path_nm: Optional[str] = None
    tbl_nm: Optional[str] = None
    col_nm: Optional[str] = None
    atch_file_rmrk_cn: Optional[str] = None

    @_before_validator("file_sz", "encr_bef_file_sz")
    def _parse_file_sizes(cls, value: Optional[str]) -> Optional[int]:
        return _parse_int(value)

    @_before_validator("dwnld_prms_yn")
    def _parse_download_flag(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_bool_yn(value)


class CommCd(BaseModel):
    # UI 라벨/필터 매핑을 위한 코드 사전 한 행.
    code_group: str
    code: str
    code_nm: str
    use_yn: bool

    @_before_validator("use_yn")
    def _parse_use_yn(cls, value: Optional[str]) -> Optional[bool]:
        parsed = _parse_bool_yn(value)
        if parsed is None:
            raise ValueError("use_yn is required")
        return parsed
