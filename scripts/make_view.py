from __future__ import annotations

import csv
from pathlib import Path


LIST_VIEW_COLUMNS = [
    "bid_pbanc_num",  # 입찰공고번호
    "bid_pbanc_nm",  # 입찰공고명
    "pbanc_stts_cd_nm",  # 공고구분
    "prcm_bsne_se_cd_nm",  # 공고분류
    "bid_mthd_cd_nm",  # 입찰방식
    "pbanc_stts_grid_cd_nm",  # 진행상태
    "pbanc_knd_cd_nm",  # 공고종류
    "std_ctrt_mthd_cd_nm",  # 계약방법
    "scsbd_mthd_cd_nm",  # 낙찰방법
]

OPENING_RESULT_VIEW_COLUMNS = [
    "ibx_onbs_rnkg",  # 순위/No
    "ibx_bzmn_reg_no",  # 사업자등록번호
    "ibx_grp_nm",  # 조달업체명
    "ibx_rprsv_nm",  # 대표자명
    "bid_ufns_rsn_nm",  # 사전판정
    "ibx_evl_scr_prpl",  # 제안서 평가점수
    "ibx_evl_scr_prce",  # 입찰 가격점수
    "ibx_evl_scr_ovrl",  # 총점
    "ibx_bdng_amt",  # 투찰금액(원)
    "ibx_slpr_rcptn_dt",  # 투찰일시
    "sfbr_slctn_rslt_cd",  # 낙찰여부(코드)
]


def is_code_column(name: str) -> bool:
    return name.endswith("_cd")


def build_view_csv(source: Path, target: Path) -> None:
    with source.open("r", newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        if reader.fieldnames is None:
            return
        if source.name == "list.csv":
            view_fieldnames = [name for name in LIST_VIEW_COLUMNS if name in reader.fieldnames]
        elif source.name == "opening_result.csv":
            view_fieldnames = [name for name in OPENING_RESULT_VIEW_COLUMNS if name in reader.fieldnames]
        else:
            view_fieldnames = [name for name in reader.fieldnames if not is_code_column(name)]
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as out_fp:
            writer = csv.DictWriter(out_fp, fieldnames=view_fieldnames)
            writer.writeheader()
            for row in reader:
                writer.writerow({key: row.get(key) for key in view_fieldnames})


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    view_dir = data_dir / "view"
    for source in data_dir.glob("*.csv"):
        target = view_dir / source.name
        build_view_csv(source, target)


if __name__ == "__main__":
    main()
