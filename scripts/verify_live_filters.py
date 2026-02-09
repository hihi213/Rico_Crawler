from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.config import load_config
from src.infrastructure.browser import BrowserController
from src.infrastructure.checkpoint import CheckpointStore
from src.infrastructure.parser import NoticeParser
from src.infrastructure.repository import NoticeRepository
from src.service.crawler_service import CrawlerService


ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")


@dataclass(frozen=True)
class FilterCombo:
    pbanc_knd_cd: Optional[str]
    pbanc_stts_cd: Optional[str]
    bid_pbanc_pgst_cd: Optional[str]

    def label(self) -> str:
        def _v(value: Optional[str]) -> str:
            return value if value else "ALL"

        return f"knd={_v(self.pbanc_knd_cd)}__stts={_v(self.pbanc_stts_cd)}__pgst={_v(self.bid_pbanc_pgst_cd)}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify live data with filter combinations.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--output-dir", default="data/verify")
    return parser.parse_args()


def build_combos() -> list[FilterCombo]:
    pbanc_knd_cds = ["공440002", "공440001"]
    pbanc_stts_cds = ["공400001", "공400002", "공400003"]
    bid_pbanc_pgst_cds = ["입160003"]
    combos: list[FilterCombo] = []
    for knd in pbanc_knd_cds:
        for stts in pbanc_stts_cds:
            for pgst in bid_pbanc_pgst_cds:
                combos.append(FilterCombo(knd, stts, pgst))
    return combos


def reset_dir(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    for csv_path in base.glob("*.csv"):
        csv_path.unlink()
    checkpoint_path = base / "checkpoint.json"
    if checkpoint_path.exists():
        checkpoint_path.unlink()


def scan_entities(paths: Iterable[Path]) -> dict[str, int]:
    hits: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            continue
        count = 0
        with path.open() as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                for value in row.values():
                    if not value:
                        continue
                    if ENTITY_RE.search(value):
                        count += 1
        hits[path.name] = count
    return hits


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    config.crawl.snapshot_enabled = False
    config.crawl.snapshot_only_list = False

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    combos = build_combos()
    results: list[dict[str, object]] = []

    with BrowserController(config.crawl) as browser:
        page = browser.new_page()
        for combo in combos:
            run_dir = output_root / combo.label()
            reset_dir(run_dir)

            config.sqlite_path = str(run_dir / "nuri.db")
            config.checkpoint_path = str(run_dir / "checkpoint.json")

            config.crawl.list_api_payload["pbancKndCd"] = combo.pbanc_knd_cd or ""
            config.crawl.list_api_payload["pbancSttsCd"] = combo.pbanc_stts_cd or ""
            config.crawl.list_api_payload["bidPbancPgstCd"] = combo.bid_pbanc_pgst_cd or ""

            config.crawl.list_filter_pbanc_knd_cd = combo.pbanc_knd_cd
            config.crawl.list_filter_pbanc_stts_cd = combo.pbanc_stts_cd
            config.crawl.list_filter_bid_pbanc_pgst_cd = combo.bid_pbanc_pgst_cd

            repo = NoticeRepository(config.sqlite_path)
            parser = NoticeParser(config.crawl.selectors)
            checkpoint = CheckpointStore(config.checkpoint_path)
            service = CrawlerService(config.crawl, repo, parser, checkpoint)

            service.run(page, args.max_pages)

            csv_paths = [
                run_dir / "bid_notice_list.csv",
                run_dir / "bid_notice_detail.csv",
                run_dir / "bid_notice_noce.csv",
                run_dir / "bid_notice_attachment.csv",
                run_dir / "bid_opening_summary.csv",
                run_dir / "bid_opening_result.csv",
            ]
            entity_hits = scan_entities(csv_paths)
            results.append(
                {
                    "combo": combo.label(),
                    "entity_hits": entity_hits,
                }
            )

    (output_root / "summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
