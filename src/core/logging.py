from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import logging  # 표준 로깅 모듈.


def setup_logging(level: str) -> None:  # 로깅 기본 설정 함수.
    logging.basicConfig(  # 전역 로깅 설정 적용.
        level=level,  # 로그 레벨 지정.
        format="%(asctime)s %(levelname)s %(name)s %(message)s",  # 로그 포맷.
    )  # basicConfig 종료.
