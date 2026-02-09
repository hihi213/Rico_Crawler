from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.domain.models import BidNoticeListItem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare snapshot list JSON with CSV output.")
    parser.add_argument("--snapshot-dir", default="data/raw", help="Directory with list_YYYYMMDD_page_*.json")
    parser.add_argument("--csv", default="data/bid_notice_list.csv", help="CSV path to compare")
    parser.add_argument("--ignore-extra", action="store_true", help="Ignore CSV rows not in snapshot")
    parser.add_argument("--sample", type=int, default=5, help="Sample mismatch count")
    parser.add_argument("--report", default=None, help="Optional JSON report output path")
    return parser.parse_args()


def build_mapping() -> dict[str, str]:
    return {
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


def normalize_row(raw: dict[str, Any], mapping: dict[str, str]) -> BidNoticeListItem:
    mapped = {mapping[k]: v for k, v in raw.items() if k in mapping}
    return BidNoticeListItem(**mapped)


def load_snapshots(snapshot_dir: Path, mapping: dict[str, str]) -> tuple[dict[tuple[str, str], dict[str, Any]], int]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    dupes = 0
    for path in sorted(snapshot_dir.glob("list_*_page_*.json")):
        payload = json.loads(path.read_text())
        for raw in payload.get("body", {}).get("result", []):
            item = normalize_row(raw, mapping)
            key = (item.bid_pbanc_no, item.bid_pbanc_ord)
            if key in rows:
                dupes += 1
            rows[key] = item.model_dump()
    return rows, dupes


def normalize_empty(value: Any) -> Any:
    if value == "":
        return None
    return value


def compare_rows(
    raw_rows: dict[tuple[str, str], dict[str, Any]],
    csv_rows: dict[tuple[str, str], dict[str, Any]],
    sample_count: int,
) -> tuple[Counter, dict[str, tuple[tuple[str, str], Any, Any]]]:
    mismatch = Counter()
    samples: dict[str, tuple[tuple[str, str], Any, Any]] = {}
    for key in raw_rows.keys() & csv_rows.keys():
        raw_row = raw_rows[key]
        csv_row = csv_rows[key]
        for field, raw_val in raw_row.items():
            csv_val = normalize_empty(csv_row.get(field))
            if raw_val != csv_val:
                mismatch[field] += 1
                if field not in samples and len(samples) < sample_count:
                    samples[field] = (key, raw_val, csv_val)
    return mismatch, samples


def load_csv(csv_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    import csv

    rows: dict[tuple[str, str], dict[str, Any]] = {}
    with csv_path.open() as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            item = BidNoticeListItem(**row)
            rows[(item.bid_pbanc_no, item.bid_pbanc_ord)] = item.model_dump()
    return rows


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("compare")

    snapshot_dir = Path(args.snapshot_dir)
    csv_path = Path(args.csv)
    mapping = build_mapping()

    raw_rows, dupes = load_snapshots(snapshot_dir, mapping)
    csv_rows = load_csv(csv_path)

    raw_keys = set(raw_rows.keys())
    csv_keys = set(csv_rows.keys())

    missing_in_csv = raw_keys - csv_keys
    extra_in_csv = csv_keys - raw_keys

    mismatch, samples = compare_rows(raw_rows, csv_rows, args.sample)

    logger.info("snapshot_rows=%s csv_rows=%s raw_dupes=%s", len(raw_rows), len(csv_rows), dupes)
    logger.info("missing_in_csv=%s extra_in_csv=%s", len(missing_in_csv), len(extra_in_csv))
    logger.info("mismatch_fields=%s", dict(mismatch))
    if samples:
        logger.info("mismatch_samples=%s", samples)

    if args.ignore_extra:
        extra_in_csv = set()

    report = {
        "snapshot_rows": len(raw_rows),
        "csv_rows": len(csv_rows),
        "raw_dupes": dupes,
        "missing_in_csv": sorted(list(missing_in_csv)),
        "extra_in_csv": sorted(list(extra_in_csv)),
        "mismatch_fields": dict(mismatch),
        "mismatch_samples": {k: [v[0], v[1], v[2]] for k, v in samples.items()},
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("report_saved path=%s", args.report)


if __name__ == "__main__":
    main()
