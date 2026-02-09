from __future__ import annotations

import logging
from typing import Any

from src.core.config import CrawlConfig

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserController:
    def __init__(self, config: CrawlConfig) -> None:
        self._config = config
        self._logger = logging.getLogger("browser")
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def __enter__(self) -> "BrowserController":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        self._context = self._browser.new_context(user_agent=self._config.user_agent)
        self._context.set_default_timeout(self._config.timeout_ms)
        self._logger.info("브라우저 컨텍스트 준비됨")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._logger.info("브라우저 컨텍스트 종료됨")
        return None

    def new_page(self) -> Any:
        if self._context is None:
            raise RuntimeError("BrowserController not initialized")
        page: Page = self._context.new_page()
        return page
