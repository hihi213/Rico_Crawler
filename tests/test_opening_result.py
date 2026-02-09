from __future__ import annotations

from src.domain.models import BidOpeningResult


def test_opening_result_score_normalization() -> None:
    item = BidOpeningResult(
        bid_pbanc_no="R26BK00000000",
        bid_pbanc_ord="000",
        bid_clsf_no="0",
        bid_prgrs_ord="000",
        ibx_onbs_rnkg=1,
        ibx_grp_nm="테스트업체",
        ibx_bdng_amt="1,000",
        ibx_slpr_rcptn_dt="2026/02/09 10:00:00",
        ibx_evl_scr_prpl=0,
        ibx_evl_scr_prce="10.5",
        ibx_evl_scr_ovrl=None,
        ibx_evl_scr_prpl_num=0,
        ibx_evl_scr_prce_num="10.5",
        ibx_evl_scr_ovrl_num=None,
    )

    assert item.ibx_evl_scr_prpl == "0"
    assert item.ibx_evl_scr_prce == "10.5"
    assert item.ibx_evl_scr_ovrl is None
    assert item.ibx_evl_scr_prpl_num == 0.0
    assert item.ibx_evl_scr_prce_num == 10.5
    assert item.ibx_evl_scr_ovrl_num is None
