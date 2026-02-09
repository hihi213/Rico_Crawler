# RiCO 누리장터 입찰공고 크롤러

누리장터 입찰공고 목록 → 상세 → 부가정보(공지/첨부/개찰)를 수집해 표준 스키마로 저장하는 크롤러입니다.  
과제 B 요구사항(안정성, 재현성, 제품 수준)을 충족하도록 재시도, 체크포인트, 중복 방지, 정규화 로직을 포함했습니다.

## 과제 맥락
- 과제 유형: ICT 인턴십 사전 과제 B (동적 크롤링)
- 목표: 동적 렌더링 페이지에서 목록/상세 핵심 필드 수집 및 표준화 저장
- 우대 사항: 재실행, 주기 실행(크론), 견고한 오류 처리

## 핵심 기능
1. 목록 → 상세 수집 파이프라인
2. 표준 스키마(파이단틱) 기반 CSV 저장
3. 날짜/금액/플래그/텍스트 정규화
4. 재시도(tenacity) + 실패 스킵 + 구조화 로그
5. 체크포인트 기반 재실행
6. 주기 실행 모드
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

## 진행 절차
1. 설치
2. 실행
3. 결과 확인

권장 Python 버전: `3.11.14`

## 1. 설치
빠른 시작 (OS 자동 감지)
```
python install.py
```

수동 설치 (운영체제 공통)
```
python -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m playwright install
```
리눅스에서 브라우저 의존성 미설치 시
```
./venv/bin/python -m playwright install --with-deps
```
윈도우에서 PowerShell 실행 정책 문제 시
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

의존성 재현성 정책
- 모든 패키지 버전은 `requirements.txt`에서 고정 관리합니다.
- 버전 변경 시 `requirements.txt`와 README의 실행 절차를 함께 업데이트합니다.

## 2. 실행
기본 실행
```
python main.py
```

실행 예시
```
python main.py -p 5
python main.py -m interval -i 3600
python main.py -r
python main.py -f knd=실공고,stts=등록공고,pgst=입찰개시
```

옵션/파라미터 정리
- `-p, --pages <N>`: 목록 페이지 수 제한 (1페이지=100건 기준)
- `-m, --mode <once|interval>`: 실행 모드
- `-i, --interval <SEC>`: 주기 실행 대기 시간(초)
- `-r, --reset`: 체크포인트 초기화
- `-f, --filter <값>`: 필터 (예: `knd=실공고,stts=등록공고,pgst=입찰개시`)
- `-c, --config <경로>`: 설정 파일 경로

## 설정(config.yaml)
주요 설정은 `config.yaml`에 있습니다. 실행 전에 바꾸지 않아도 됩니다.
설정 변경은 `config.yaml`을 직접 편집하세요.
- `set`은 타입 검증 후 변경하며, 변경 전/후 값을 함께 출력합니다.
- `search_range_days`: 최근 N일 범위 자동 계산
- `max_pages`: 페이지 제한
- `snapshot_enabled`: 원본 JSON 저장 여부
- `snapshot_mode`: 예상 외 필드 감지 시 저장 또는 전체 저장
- `list_api_payload`: 검색 조건(날짜/필터 등)

필터는 기본적으로 비워두고 전체 수집을 권장합니다.  
빠른 확인이 필요할 때만 CLI 옵션으로 필터를 좁혀 수집 범위를 제한하세요.

## 3. 결과 확인
CSV 저장 위치: `data/`  
샘플 결과: `sample/` (제출용 증빙. 실제 실행 결과는 `data/`에 생성됨)  
실행 후 아래 파일이 생성되면 정상 동작입니다.
- `data/list.csv`: 입찰공고 목록
- `data/detail.csv`: 입찰공고 상세
- `data/notice.csv`: 공지/유의사항
- `data/attachments.csv`: 첨부파일 메타데이터
- `data/opening_summary.csv`: 개찰 요약
- `data/opening_result.csv`: 개찰 결과 상세

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
- 실제 실행일 기준 확인(예: 샘플 생성일 기준 1페이지 수집 확인)
- 필터 조합은 대표성 기준으로 선택(상태/종류 분포 확인 목적)

## 테스트 전략(최소 범위)
- 수집 파이프라인: 목록 → 상세 → 공지/첨부/개찰 전체 흐름
- 정규화 규칙: 날짜/금액/플래그/텍스트 디코딩
- 재시도/체크포인트: 실패 재시도 및 중단 후 재실행

실행 방법
```
pytest -q
```

## 필터 조합 기준(대표성)
대표성/상태 분포 확인을 위해 조합을 구성하며, 최소 6개는 아래 범주를 모두 포함하기 위한 수입니다.
- 공고종류: 모의공고/실공고
- 공고구분: 등록/변경/취소/재공고
- 진행상태: 입찰개시/개찰중/개찰완료/유찰/재입찰/낙찰자선정

## 문서
- 결정 기록: `docs/decision_log.md`
- 트러블슈팅: `docs/troubleshooting.md`
- 스키마: `docs/schema.md`

## 한계 및 향후 개선
1. 성능 및 아키텍처
- 현황: Playwright sync_api 단일 스레드
- 개선: asyncio + playwright.async_api로 병렬 수집 파이프라인

2. 운영 및 스케줄링
- 현황: 주기 실행 모드에서 time.sleep 기반 루프
- 개선: cron/systemd timer 등 외부 스케줄러 위임

3. 데이터 관측성 및 신뢰성
- 현황: WebSquare 특성상 필드 누락/빈 값 발생 가능
- 개선: 모델 유효성 실패 시 원본 스냅샷 저장 강화

4. 보안 및 차단 회피
- 현황: 고정 User-Agent, 단일 IP
- 개선: 프록시 로테이션, User-Agent 랜덤화

5. 첨부파일 저장
- 현황: 메타데이터만 저장
- 개선: 실제 파일 다운로드 및 저장

## 보안 참고 (Mend 경고)
Mend.io 기준 `pytest==9.0.2` 관련 CVE-2025-71176 경고가 보고될 수 있습니다.  
현재 PyPI 최신 버전이 9.0.2라서 단순 업그레이드로 해소되지 않으며, 향후 업데이트를 권장합니다.
