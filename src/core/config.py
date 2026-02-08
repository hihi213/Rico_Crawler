from __future__ import annotations  # 타입 힌트 전방 참조 허용.

from pathlib import Path  # 파일 경로 처리를 위한 표준 모듈.
from typing import Any, Optional  # 선택적 타입 표현.

import yaml  # YAML 파서.
from pydantic import BaseModel, Field  # 설정 모델과 기본값 처리.


class DetailSelectors(BaseModel):  # 상세 페이지 셀렉터 묶음.
    budget_amount: Optional[str] = None  # 예산 금액 셀렉터.
    bid_start_at: Optional[str] = None  # 입찰 시작일 셀렉터.
    bid_end_at: Optional[str] = None  # 입찰 마감일 셀렉터.


class Selectors(BaseModel):  # 목록/상세 공통 셀렉터 정의.
    list_row: str  # 목록 행 셀렉터.
    list_link: str  # 목록 링크 셀렉터.
    search_button: Optional[str] = None  # 목록 검색 버튼 셀렉터.
    list_notice_no: Optional[str] = None  # 공고번호 셀렉터.
    list_title: Optional[str] = None  # 공고명 셀렉터.
    list_published_at: Optional[str] = None  # 게시일 셀렉터.
    list_agency: Optional[str] = None  # 기관명 셀렉터.
    pagination_next: Optional[str] = None  # 다음 페이지 셀렉터.
    detail_popup: Optional[str] = None  # 상세 팝업 컨테이너 셀렉터.
    detail_close: Optional[str] = None  # 상세 팝업 닫기 셀렉터.
    detail_fields: DetailSelectors = Field(default_factory=DetailSelectors)  # 상세 셀렉터 그룹.


class CrawlConfig(BaseModel):  # 크롤링 설정 모델.
    base_url: str  # 기본 URL.
    list_url: str  # 목록 URL.
    list_api_url: Optional[str] = None  # 목록 API URL.
    detail_api_url: str  # 상세 API URL.
    max_pages: int  # 최대 페이지 수.
    timeout_ms: int  # 타임아웃(ms).
    retry_count: int  # 재시도 횟수.
    retry_backoff_sec: float  # 재시도 백오프.
    user_agent: str  # 사용자 에이전트.
    list_api_headers: dict[str, str] = Field(default_factory=dict)  # 목록 API 헤더.
    list_api_payload: dict[str, Any] = Field(default_factory=dict)  # 목록 API payload.
    selectors: Selectors  # 셀렉터 설정.


class AppConfig(BaseModel):  # 애플리케이션 루트 설정.
    crawl: CrawlConfig  # 크롤링 설정.
    sqlite_path: str  # SQLite 경로.
    checkpoint_path: str = "data/checkpoint.json"  # 체크포인트 경로.
    log_level: str  # 로그 레벨.


def load_config(path: str) -> AppConfig:  # 설정 파일 로더.
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))  # YAML 읽기.
    if hasattr(AppConfig, "model_validate"):  # Pydantic v2 지원 여부 확인.
        return AppConfig.model_validate(data)  # v2 방식으로 파싱.
    return AppConfig.parse_obj(data)  # v1 방식으로 파싱.
