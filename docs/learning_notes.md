# 파일별 이해 기록

## main.py
- 역할: CLI 진입점에서 설정 로드, 의존성 초기화, 실행 모드(once/interval) 제어.
- 흐름:
  1) CLI 인자 파싱
  2) 설정 로드 및 로깅 초기화
  3) Repository/Parser/Checkpoint/Service 생성
  4) BrowserController 컨텍스트에서 크롤링 실행

## config.yaml
- 역할: 모든 크롤링/저장/재시도/페이로드/헤더 설정을 한 곳에서 관리.
- 핵심:
  - list/detail/noce/attachment/opening API URL과 payload 템플릿
  - recordCountPerPage로 목록 페이지 크기 제어
  - 체크포인트/로그 레벨 설정

## src/service/crawler_service.py
- 역할: 크롤링 전체 흐름을 통합 실행(목록/상세/공지/첨부/개찰 수집 및 저장).
- 흐름:
  1) 체크포인트로 시작 페이지 결정
  2) 목록 API 호출 → 목록 모델 생성
  3) 상세/공지/첨부/개찰 API 호출 → 모델 생성
  4) CSV 저장 후 체크포인트 갱신
- 추가: search_range_days가 있으면 동적 날짜 계산, 없으면 고정 날짜 유효성 검증

## src/infrastructure/parser.py
- 역할: API 응답에서 필요한 원본 맵을 추출하는 파서.
- 흐름:
  1) 목록 DOM → col_id 기반 원본 맵 생성
  2) 상세/공지/개찰/첨부 응답에서 핵심 리스트/맵만 추출

## src/infrastructure/repository.py
- 역할: CSV 저장과 중복 방지(키 캐시)를 담당.
- 흐름:
  1) 기존 CSV에서 중복 키 로드
  2) 신규 행만 필터링
  3) CSV에 append 저장

## src/infrastructure/browser.py
- 역할: Playwright 브라우저/컨텍스트 생성과 종료 관리.
- 흐름:
  1) Playwright 실행 → Chromium 컨텍스트 생성
  2) 기본 타임아웃/UA 설정
  3) 작업 후 자원 정리

## src/infrastructure/checkpoint.py
- 역할: 중단 복구를 위한 체크포인트(JSON) 저장/로드.
- 흐름:
  1) JSON 파일 존재 여부 확인
  2) current_page를 읽어 유효성 확인
  3) 저장 시 임시 파일에 기록 후 원자적 교체

## src/domain/models.py
- 역할: API 응답을 스키마에 맞게 정규화하는 Pydantic 도메인 모델.
- 흐름:
  1) 공통 파서(_parse_* / _normalize_*)로 날짜/숫자/플래그 정규화
  2) 목록/상세/개찰/첨부/공지 모델에 적용
  3) 개찰 점수는 문자열+숫자 병행 저장
