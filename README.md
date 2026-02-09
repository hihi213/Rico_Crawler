# RiCO 누리장터 입찰공고 크롤러

누리장터 입찰공고 목록 → 상세 → 부가정보(공지/첨부/개찰)를 수집해 표준 스키마로 저장하는 크롤러입니다.  
과제 B 요구사항(안정성, 재현성, 제품 수준)을 충족하도록 재시도, 체크포인트, 중복 방지, 정규화 로직을 포함했습니다.

## 핵심 기능
1. 목록 → 상세 수집 파이프라인
2. 표준 스키마(Pydantic) 기반 CSV 저장
3. 날짜/금액/플래그/텍스트 정규화
4. 재시도(tenacity) + 실패 스킵 + 로그 기록
5. 체크포인트 기반 재실행
6. interval 실행 모드
7. 필터 옵션(공고종류/공고상태/진행상태) 지원

## 폴더 구조
```
src/
  domain/            # Pydantic 모델
  infrastructure/    # 브라우저/파서/저장소/체크포인트
  service/           # 수집 로직
  core/              # 설정/로깅
data/                # CSV 결과/체크포인트/스냅샷
docs/                # 결정 기록/트러블슈팅/스키마
```

## 실행 방법
### 1) 가상환경 + 의존성 설치
```
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m playwright install
```

Windows:
```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m playwright install
```

### 2) 기본 실행 (전체 수집)
```
./venv/bin/python main.py --max-pages 2
```

### 3) 필터 옵션 실행
```
./venv/bin/python main.py --max-pages 2 \
  --filter-pbanc-knd-cd 공440002 \
  --filter-pbanc-stts-cd 공400001 \
  --filter-bid-pgst-cd 입160003
```

### 4) interval 모드
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

## 출력 파일
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

## 재현성/안정성
1. 페이지 단위 체크포인트 저장으로 중단 후 재실행 가능
2. 재시도(tenacity)로 네트워크/타임아웃 오류 대응
3. 중복 키 기준 저장으로 중복 방지

## 실동작 검증
- 2026-02-09 기준 실제 누리장터에서 1페이지(100건) 수집 확인
- 필터 조합 6개 × 2페이지 수집 후 HTML 엔티티 전수 스캔 0건 확인



## 문서
- 결정 기록: `docs/decision_log.md`
- 트러블슈팅: `docs/troubleshooting.md`
- 스키마: `docs/schema.md`

## 한계 및 향후 개선
1. 대량 데이터 처리 시 비동기/병렬화 도입 필요
2. 운영 스케줄링은 cron/systemd 전환 권장
3. 첨부파일은 메타데이터만 저장 (다운로드는 미구현)
4. 상세 하위 리스트 확장(추가 스키마 필요)


## 보안 참고 (Mend 경고)
Mend.io 기준 `pytest==9.0.2` 관련 CVE-2025-71176 경고가 보고될 수 있습니다.  
현재 PyPI 최신 버전이 9.0.2라서 단순 업그레이드로 해소되지 않으며, 향후 업데이트를 권장합니다.
