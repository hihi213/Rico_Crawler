# RiCO 누리장터 입찰공고 크롤러

누리장터 입찰공고 목록 → 상세 → 부가정보(공지/첨부/개찰)를 수집해 표준 스키마로 저장하는 크롤러입니다.  
과제 B 요구사항(안정성, 재현성, 제품 수준)을 충족하도록 재시도, 체크포인트, 중복 방지, 정규화 로직을 포함했습니다.

## 과제 맥락
- 과제 유형: ICT Internship 사전 과제 B (동적 크롤링)
- 목표: 동적 렌더링 페이지에서 목록/상세 핵심 필드 수집 및 표준화 저장
- 우대 사항: 재실행, interval/cron 모드, 견고한 오류 처리

## 핵심 기능
1. 목록 → 상세 수집 파이프라인
2. 표준 스키마(Pydantic) 기반 CSV 저장
3. 날짜/금액/플래그/텍스트 정규화
4. 재시도(tenacity) + 실패 스킵 + 구조화 로그
5. 체크포인트 기반 재실행
6. interval 실행 모드
7. 필터 옵션(공고종류/공고상태/진행상태)

## 폴더 구조
```
src/
  domain/            # Pydantic 모델
  infrastructure/    # 브라우저/파서/저장소/체크포인트
  service/           # 수집 로직
  core/              # 설정/로깅
main.py              # CLI 진입점
data/                # CSV 결과/체크포인트/스냅샷
docs/                # 결정 기록/트러블슈팅/스키마
```

## 재현 절차
재현 절차 요약: venv 생성 → 설치 → 실행 → 결과 확인
1. 권장 Python 버전: `3.11.14`

macOS (Apple Silicon/Intel 공통)
1. venv 생성
```
python3 -m venv venv
```
2. 의존성 설치
```
./venv/bin/pip install -r requirements.txt
```
3. Playwright 설치
```
./venv/bin/python -m playwright install
```
4. 시스템 권한 팝업이 뜨면 허용

Windows
1. venv 생성
```
python -m venv venv
```
2. 의존성 설치
```
venv\Scripts\pip install -r requirements.txt
```
3. Playwright 설치
```
venv\Scripts\python -m playwright install
```
4. PowerShell 실행 정책 문제 시
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Linux
1. venv 생성
```
python3 -m venv venv
```
2. 의존성 설치
```
./venv/bin/pip install -r requirements.txt
```
3. Playwright 설치
```
./venv/bin/python -m playwright install --with-deps
```

의존성 재현성 정책
- 모든 패키지 버전은 `requirements.txt`에서 고정 관리합니다.
- 버전 변경 시 `requirements.txt`와 README의 실행 절차를 함께 업데이트합니다.

## 실행
기본 실행 (전체 수집)
```
./venv/bin/python main.py --max-pages 2
```

필터 옵션 실행
```
./venv/bin/python main.py --max-pages 2 \
  --filter-pbanc-knd-cd 공440002 \
  --filter-pbanc-stts-cd 공400001 \
  --filter-bid-pgst-cd 입160003
```

interval 모드
```
./venv/bin/python main.py --mode interval --interval-sec 3600
```

## 설정(config.yaml)
주요 설정은 `config.yaml`에 있습니다.
- `search_range_days`: 최근 N일 범위 자동 계산
- `max_pages`: 페이지 제한
- `snapshot_enabled`: 원본 JSON 저장 여부
- `snapshot_mode`: 예상 외 필드 감지 시 저장 또는 전체 저장
- `list_api_payload`: 검색 조건(날짜/필터 등)

필터는 기본적으로 비워두고 전체 수집을 권장합니다.  
필요 시 CLI 옵션으로 필터를 좁혀서 수집 범위를 제한할 수 있습니다.

## 결과 확인
출력 경로/파일명 규칙: `data/*.csv`
CSV는 `data/` 아래에 생성됩니다.
- `data/bid_notice_list.csv`
- `data/bid_notice_detail.csv`
- `data/bid_notice_noce.csv`
- `data/bid_notice_attachment.csv`
- `data/bid_opening_summary.csv`
- `data/bid_opening_result.csv`

스키마 정의는 `docs/schema.md`에 있습니다.

## 정규화 규칙
1. 날짜/시간: 다양한 포맷을 `datetime`으로 변환
2. 금액: 콤마 제거 후 `int`
3. Y/N 플래그: `bool` 변환
4. 문서번호: 공백 제거 + HTML 엔티티 디코딩
5. 텍스트: HTML 엔티티 디코딩

## 안정성/재실행
1. 페이지 단위 체크포인트 저장으로 중단 후 재실행 가능
2. 재시도(tenacity)로 네트워크/타임아웃 오류 대응
3. 중복 키 기준 저장으로 중복 방지

## 스냅샷 (변경 감지)
상세 응답이 빈 필드로 내려오는 경우가 있어, 예상 외 키 감지 시 원본 JSON을 선택 저장하도록 구현했습니다.
- 목록: `snapshot_mode=all`일 때 목록 원본 저장
- 상세/개찰: 예상 외 키 감지 시 저장
- 저장 위치: `snapshot_dir` (기본 `data/raw`)

## 실동작
- 2026-02-09 기준 실제 누리장터에서 1페이지(100건) 수집 확인
- 필터 조합 6개 × 2페이지 수집 후 HTML 엔티티 전수 스캔 0건 확인

## 문서
- 결정 기록: `docs/decision_log.md`
- 트러블슈팅: `docs/troubleshooting.md`
- 스키마: `docs/schema.md`

## 한계 및 향후 개선
1. 성능 및 아키텍처
- 현황: Playwright sync_api 단일 스레드
- 개선: asyncio + playwright.async_api로 병렬 수집 파이프라인

2. 운영 및 스케줄링
- 현황: interval 모드에서 time.sleep 기반 루프
- 개선: cron/systemd timer 등 외부 스케줄러 위임

3. 데이터 관측성 및 신뢰성
- 현황: WebSquare 특성상 필드 누락/빈 값 발생 가능
- 개선: 모델 유효성 실패 시 raw snapshot 저장 강화

4. 보안 및 차단 회피
- 현황: 고정 User-Agent, 단일 IP
- 개선: Proxy Rotation, User-Agent 랜덤화

5. 첨부파일 저장
- 현황: 메타데이터만 저장
- 개선: 실제 파일 다운로드 및 저장

## 보안 참고 (Mend 경고)
Mend.io 기준 `pytest==9.0.2` 관련 CVE-2025-71176 경고가 보고될 수 있습니다.  
현재 PyPI 최신 버전이 9.0.2라서 단순 업그레이드로 해소되지 않으며, 향후 업데이트를 권장합니다.
