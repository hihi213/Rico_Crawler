from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class DetailSelectors(BaseModel):
    budget_amount: Optional[str] = None
    bid_start_at: Optional[str] = None
    bid_end_at: Optional[str] = None


class Selectors(BaseModel):
    list_row: str
    list_link: str
    search_button: Optional[str] = None
    list_notice_no: Optional[str] = None
    list_title: Optional[str] = None
    list_published_at: Optional[str] = None
    list_agency: Optional[str] = None
    pagination_next: Optional[str] = None
    detail_popup: Optional[str] = None
    detail_close: Optional[str] = None
    detail_fields: DetailSelectors = Field(default_factory=DetailSelectors)


class CrawlConfig(BaseModel):
    base_url: str
    list_url: str
    list_api_url: Optional[str] = None
    detail_api_url: str
    noce_api_url: Optional[str] = None
    attachment_api_url: Optional[str] = None
    opening_api_url: Optional[str] = None
    max_pages: int
    timeout_ms: int
    retry_count: int
    retry_backoff_sec: float
    user_agent: str
    search_range_days: Optional[int] = None
    snapshot_enabled: bool = False
    snapshot_dir: str = "data/snapshots"
    snapshot_mode: str = "unexpected"
    snapshot_only_list: bool = False
    list_filter_pbanc_knd_cd: Optional[str] = None
    list_filter_pbanc_stts_cd: Optional[str] = None
    list_filter_bid_pbanc_pgst_cd: Optional[str] = None
    list_api_headers: dict[str, str] = Field(default_factory=dict)
    list_api_payload: dict[str, Any] = Field(default_factory=dict)
    detail_api_headers: dict[str, str] = Field(default_factory=dict)
    detail_api_payload: dict[str, Any] = Field(default_factory=dict)
    noce_api_headers: dict[str, str] = Field(default_factory=dict)
    noce_api_payload: dict[str, Any] = Field(default_factory=dict)
    attachment_api_headers: dict[str, str] = Field(default_factory=dict)
    attachment_api_payload: dict[str, Any] = Field(default_factory=dict)
    opening_api_headers: dict[str, str] = Field(default_factory=dict)
    opening_api_payload: dict[str, Any] = Field(default_factory=dict)
    selectors: Selectors


class AppConfig(BaseModel):
    crawl: CrawlConfig
    sqlite_path: str
    checkpoint_path: str = "data/checkpoint.json"
    log_level: str


def load_config(path: str) -> AppConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if hasattr(AppConfig, "model_validate"):
        return AppConfig.model_validate(data)
    return AppConfig.parse_obj(data)
