from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class DetailSelectors(BaseModel):
    budget_amount: Optional[str] = None
    bid_start_at: Optional[str] = None
    bid_end_at: Optional[str] = None


class Selectors(BaseModel):
    list_row: str
    list_link: str
    list_notice_no: Optional[str] = None
    list_title: Optional[str] = None
    list_published_at: Optional[str] = None
    list_agency: Optional[str] = None
    pagination_next: Optional[str] = None
    detail_fields: DetailSelectors = Field(default_factory=DetailSelectors)


class CrawlConfig(BaseModel):
    base_url: str
    list_url: str
    max_pages: int
    timeout_ms: int
    retry_count: int
    retry_backoff_sec: float
    user_agent: str
    selectors: Selectors


class AppConfig(BaseModel):
    crawl: CrawlConfig
    sqlite_path: str
    log_level: str


def load_config(path: str) -> AppConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if hasattr(AppConfig, "model_validate"):
        return AppConfig.model_validate(data)
    return AppConfig.parse_obj(data)
