from __future__ import annotations

import argparse
import logging
import time

from src.core.config import load_config
from src.core.logging import setup_logging
from src.infrastructure.browser import BrowserController
from src.infrastructure.parser import NoticeParser
from src.infrastructure.repository import NoticeRepository
from src.service.crawler_service import CrawlerService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RiCO Nuri Notice Crawler")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--mode", choices=["once", "interval"], default="once")
    parser.add_argument("--interval-sec", type=int, default=3600)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    repo = NoticeRepository(config.sqlite_path)
    parser = NoticeParser(config.crawl.selectors)
    service = CrawlerService(config.crawl, repo, parser)

    with BrowserController(config.crawl) as browser:
        page = browser.new_page()
        if args.mode == "once":
            service.run(page, args.max_pages)
        else:
            while True:
                logger.info("interval crawl start")
                service.run(page, args.max_pages)
                logger.info("interval crawl sleep=%s sec", args.interval_sec)
                time.sleep(args.interval_sec)


if __name__ == "__main__":
    main()
