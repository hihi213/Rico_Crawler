from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import argparse  # CLI 인자 파싱.
import logging  # 로깅.
import time  # interval 모드 대기.

from src.core.config import load_config  # 설정 로더.
from src.core.logging import setup_logging  # 로깅 설정.
from src.infrastructure.browser import BrowserController  # 브라우저 컨트롤러.
from src.infrastructure.checkpoint import CheckpointStore  # 체크포인트.
from src.infrastructure.parser import NoticeParser  # 파서.
from src.infrastructure.repository import NoticeRepository  # 저장소.
from src.service.crawler_service import CrawlerService  # 서비스.


def parse_args() -> argparse.Namespace:  # CLI 인자 파싱 함수.
    parser = argparse.ArgumentParser(description="RiCO Nuri Notice Crawler")  # 파서 생성.
    parser.add_argument("--config", default="config.yaml")  # 설정 파일 경로.
    parser.add_argument("--max-pages", type=int, default=None)  # 최대 페이지 제한.
    parser.add_argument("--mode", choices=["once", "interval"], default="once")  # 실행 모드.
    parser.add_argument("--interval-sec", type=int, default=3600)  # 주기(초).
    return parser.parse_args()  # 파싱 결과 반환.


def main() -> None:  # 메인 진입점.
    args = parse_args()  # 인자 파싱.
    config = load_config(args.config)  # 설정 로드.
    setup_logging(config.log_level)  # 로깅 설정 적용.
    logger = logging.getLogger("main")  # 로거 생성.

    repo = NoticeRepository(config.sqlite_path)  # 저장소 초기화.
    parser = NoticeParser(config.crawl.selectors)  # 파서 초기화.
    checkpoint = CheckpointStore(config.checkpoint_path)  # 체크포인트 저장소.
    service = CrawlerService(config.crawl, repo, parser, checkpoint)  # 서비스 초기화.

    with BrowserController(config.crawl) as browser:  # 브라우저 컨텍스트 시작.
        page = browser.new_page()  # 새 페이지 생성.
        if args.mode == "once":  # 단발 실행.
            service.run(page, args.max_pages)  # 크롤링 실행.
        else:  # interval 실행.
            while True:  # 반복 실행.
                logger.info("interval crawl start")  # 시작 로그.
                service.run(page, args.max_pages)  # 크롤링 실행.
                logger.info("interval crawl sleep=%s sec", args.interval_sec)  # 대기 로그.
                time.sleep(args.interval_sec)  # 설정된 시간만큼 대기.


if __name__ == "__main__":  # 스크립트 직접 실행 시.
    main()  # 메인 호출.
