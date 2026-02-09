from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import argparse  # CLI 인자 파싱.
import logging  # 로깅.
import sys  # 종료 코드.
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
    parser.add_argument("-c", "--config", default="config.yaml")  # 설정 파일 경로.
    parser.add_argument("-p", "--pages", type=int, default=None)  # 최대 페이지 제한.
    parser.add_argument("-m", "--mode", choices=["once", "interval"], default="once")  # 실행 모드.
    parser.add_argument("-i", "--interval", type=int, default=3600)  # 주기(초).
    parser.add_argument(
        "-f",
        "--filter",
        default=None,
        help="필터: knd=실공고,stts=등록공고,pgst=입찰개시",
    )
    parser.add_argument("-r", "--reset", action="store_true")  # 체크포인트 초기화.
    return parser.parse_args()  # 파싱 결과 반환.


KND_MAP = {
    "모의공고": "공440001",
    "실공고": "공440002",
}

STTS_MAP = {
    "등록공고": "공400001",
    "변경공고": "공400002",
    "취소공고": "공400003",
    "재공고": "공400004",
}

PGST_MAP = {
    "입찰개시": "입160003",
    "개찰중": "입160001",
    "개찰완료": "입160002",
    "접수완료": "입160004",
    "유찰": "입160005",
    "재입찰": "입160006",
    "낙찰자선정": "입160010",
    "작성중": "진010021",
}


def normalize_filter_value(value: str, mapping: dict[str, str]) -> str:
    if value in mapping:
        return mapping[value]
    if value in mapping.values():
        return value
    return ""


def parse_filter(value: str, logger: logging.Logger) -> dict[str, str]:
    if not value:
        return {}
    result: dict[str, str] = {}
    parts = [part.strip() for part in value.split(",") if part.strip()]
    for part in parts:
        if "=" not in part:
            logger.error("필터 형식 오류: %s (예: knd=실공고)", part)
            sys.exit(2)
        key, raw_value = [item.strip() for item in part.split("=", 1)]
        if key == "knd":
            code = normalize_filter_value(raw_value, KND_MAP)
            if not code:
                logger.error("공고종류 값 오류: %s (가능: %s)", raw_value, ", ".join(KND_MAP.keys()))
                sys.exit(2)
            result["pbancKndCd"] = code
        elif key == "stts":
            code = normalize_filter_value(raw_value, STTS_MAP)
            if not code:
                logger.error("공고구분 값 오류: %s (가능: %s)", raw_value, ", ".join(STTS_MAP.keys()))
                sys.exit(2)
            result["pbancSttsCd"] = code
        elif key == "pgst":
            code = normalize_filter_value(raw_value, PGST_MAP)
            if not code:
                logger.error("진행상태 값 오류: %s (가능: %s)", raw_value, ", ".join(PGST_MAP.keys()))
                sys.exit(2)
            result["bidPbancPgstCd"] = code
        else:
            logger.error("알 수 없는 필터 키: %s (사용 가능: knd, stts, pgst)", key)
            sys.exit(2)
    return result


def main() -> None:  # 메인 진입점.
    args = parse_args()  # 인자 파싱.
    config = load_config(args.config)  # 설정 로드.
    setup_logging(config.log_level)  # 로깅 설정 적용.
    logger = logging.getLogger("main")  # 로거 생성.

    filters = parse_filter(args.filter, logger)
    if "pbancKndCd" in filters:
        config.crawl.list_api_payload["pbancKndCd"] = filters["pbancKndCd"]
        config.crawl.list_filter_pbanc_knd_cd = filters["pbancKndCd"]
        logger.info("CLI 필터 적용: 공고종류=%s", filters["pbancKndCd"])
    if "pbancSttsCd" in filters:
        config.crawl.list_api_payload["pbancSttsCd"] = filters["pbancSttsCd"]
        config.crawl.list_filter_pbanc_stts_cd = filters["pbancSttsCd"]
        logger.info("CLI 필터 적용: 공고상태=%s", filters["pbancSttsCd"])
    if "bidPbancPgstCd" in filters:
        config.crawl.list_api_payload["bidPbancPgstCd"] = filters["bidPbancPgstCd"]
        config.crawl.list_filter_bid_pbanc_pgst_cd = filters["bidPbancPgstCd"]
        logger.info("CLI 필터 적용: 진행상태=%s", filters["bidPbancPgstCd"])

    repo = NoticeRepository(config.sqlite_path)  # 저장소 초기화.
    parser = NoticeParser(config.crawl.selectors)  # 파서 초기화.
    checkpoint = CheckpointStore(config.checkpoint_path)  # 체크포인트 저장소.
    service = CrawlerService(config.crawl, repo, parser, checkpoint)  # 서비스 초기화.

    with BrowserController(config.crawl) as browser:  # 브라우저 컨텍스트 시작.
        page = browser.new_page()  # 새 페이지 생성.
        if args.mode == "once":  # 단발 실행.
            if args.reset:
                checkpoint.clear()
                logger.info("체크포인트 초기화")
            service.run(page, args.pages)  # 크롤링 실행.
        else:  # interval 실행.
            while True:  # 반복 실행.
                logger.info("주기 실행 시작")  # 시작 로그.
                if args.reset:
                    checkpoint.clear()
                    logger.info("체크포인트 초기화")
                service.run(page, args.pages)  # 크롤링 실행.
                logger.info("주기 대기=%s초", args.interval)  # 대기 로그.
                time.sleep(args.interval)  # 설정된 시간만큼 대기.


if __name__ == "__main__":  # 스크립트 직접 실행 시.
    main()  # 메인 호출.
