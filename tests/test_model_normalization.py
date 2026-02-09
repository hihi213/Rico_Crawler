from __future__ import annotations

from src.domain.models import AttachmentItem, BidNoticeListItem


def test_list_item_datetime_and_flags() -> None:
    item = BidNoticeListItem(
        bid_pbanc_no="R26BK01292424",
        bid_pbanc_ord="001",
        bid_pbanc_nm="테스트 공고",
        bid_pbanc_num="R26BK01292424-001",
        pbanc_stts_cd="01",
        pbanc_stts_cd_nm="등록공고",
        prcm_bsne_se_cd="A",
        prcm_bsne_se_cd_nm="용역",
        bid_mthd_cd="B",
        bid_mthd_cd_nm="일반경쟁",
        std_ctrt_mthd_cd="C",
        std_ctrt_mthd_cd_nm="일반",
        scsbd_mthd_cd="D",
        scsbd_mthd_cd_nm="적격심사",
        grp_nm="기관",
        pbanc_pstg_dt="2026/02/06 19:11",
        slpr_rcpt_ddln_dt="2026/02/07 10:00",
        pbanc_knd_cd="E",
        pbanc_knd_cd_nm="신규",
        pbanc_stts_grid_cd_nm="입찰개시",
        row_num=1,
        tot_cnt=1,
        current_page=1,
        record_count_per_page=10,
        next_row_yn="Y",
        pbanc_pstg_yn="N",
    )

    assert item.pbanc_pstg_dt.year == 2026
    assert item.slpr_rcpt_ddln_dt is not None
    assert item.next_row_yn is True
    assert item.pbanc_pstg_yn is False


def test_attachment_inpt_dt_parsing() -> None:
    item = AttachmentItem(
        unty_atch_file_no="A",
        atch_file_sqno=1,
        bsne_clsf_cd="업130031",
        atch_file_nm="test.pdf",
        orgnl_atch_file_nm="test.pdf",
        file_extn_nm=".pdf",
        file_sz="1,024",
        inpt_dt="2026/02/09 10:00:00",
    )

    assert item.inpt_dt is not None
    assert item.file_sz == 1024
