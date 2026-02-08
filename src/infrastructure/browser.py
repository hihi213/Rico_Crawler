from __future__ import annotations  # 타입 힌트 전방 참조 허용.

import logging  # 로깅.
from typing import Any  # 범용 타입.

from src.core.config import CrawlConfig  # 크롤링 설정 모델.

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserController:  # 브라우저 제어 인터페이스.
    def __init__(self, config: CrawlConfig) -> None:  # 설정 주입.
        self._config = config  # 설정 보관.
        self._logger = logging.getLogger("browser")  # 로거 생성.
        self._playwright: Playwright | None = None  # Playwright 핸들.
        self._browser: Browser | None = None  # 브라우저 핸들.
        self._context: BrowserContext | None = None  # 컨텍스트 핸들.

    def __enter__(self) -> "BrowserController":  # 컨텍스트 매니저 진입.
        # sync_playwright() 호출해 받은 객체에 대해 start()실행
        self._playwright = sync_playwright().start()  # Playwright 런타임을 시작해 드라이버를 초기화한다.
        self._browser = self._playwright.chromium.launch()  # Chromium을 실행해 세션을 연다.
        self._context = self._browser.new_context(  # 컨텍스트 생성으로 브라우저 내부에 독립적인 세션을 생성해 이전 크롤링의 쿠키나 캐시가 다음작업에 영향을 주지 않도록
            user_agent=self._config.user_agent,  # 사용자 에이전트 적용해 User-Agent를 설정해 실제 브라우저인것처럼 속여 봇 차단 로직을 회피
        )
        self._context.set_default_timeout(self._config.timeout_ms)  # 페이지/요소 대기의 기본 타임아웃을 통일한다.
        self._logger.info("browser_context_ready")  # 브라우저 컨텍스트 준비 완료 로그.
        return self  # 자신 반환.

    def __exit__(self, exc_type, exc, tb) -> None:  # 컨텍스트 매니저 종료.
        if self._context is not None:  # 컨텍스트가 있으면.
            self._context.close()  # 컨텍스트 종료.
        if self._browser is not None:  # 브라우저가 있으면.
            self._browser.close()  # 브라우저 종료.
        if self._playwright is not None:  # Playwright가 있으면.
            self._playwright.stop()  # Playwright 종료.
        self._logger.info("browser_context_closed")  # 자원 정리 완료 로그.
        return None  # 예외 전파.

    def new_page(self) -> Any:  # 새 페이지 생성.
        if self._context is None:  # 컨텍스트가 없으면.
            raise RuntimeError("BrowserController not initialized")  # 초기화 오류.
        page: Page = self._context.new_page()  # 새 탭을 열어 크롤링 단위를 분리한다.
        return page  # 페이지 반환.
