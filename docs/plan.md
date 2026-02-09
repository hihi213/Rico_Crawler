## 큰 계획
## 1단계: 요구사항 & 스키마 정의 (Day 1 오전)

- [x] 누리장터 실제 페이지 보면서 필드 리스트업
    - notice_id, title, organization, amount, date, region, category, url 등
- 스키마 정의/보완(필수)
    - 필수
        - [x] 상세 스키마 확정: `BidNoticeDetail` 필드 리스트 1차 확정 + JSON 필드명/도메인 매핑 표 작성
        - [x] 날짜/금액/플래그 정규화 규칙 확장: 실제 포맷별 파서 규칙 명시
        - [x] 응답 envelope 모델 추가: 관찰된 공통 응답 구조를 정의 
        - [x] 고유키/관계 정의: 공고-첨부-개찰결과 FK/PK 관계
        - [x] 테스트 기준 추가: 스키마 샘플 최소 건수 + 필수/선택 필드 검증 케이스 정의
    - 권장
        - [x] 목록/상세 공통 키 정리: `bidPbancMap`/`pbancOrgMap`/목록행 공통 필드 모델 분리
        - [x] 코드/코드명 사전: `CommCd` 코드 테이블 스키마 정의
        - [x] 미확정 항목 트래킹: `2.1.2 추가 수집 필요 항목`을 상태/샘플/결론 표로 관리
        - [x] 개찰결과 모델 추가: `oobsRsltList` + 요약(`pbancMap`) 엔티티 정의 및 연결키 명시
    - 보류(범위 외/후순위)
        - 첨부 다운로드 규칙 명확화: `k00` 입력값/우선순위/실패시 폴백 표로 정리
        - 리스트 중복 제거 정책: 제한/조건 리스트별 유니크 기준 명시
        - 스키마 버전 관리: `schema_version`/`last_updated` 표기 추가
        - 국제화/문자셋 고려: 텍스트 필드 길이/문자 제한 기준 제안
- Pydantic 모델 설계
    - [x] `BidNotice` 모델 + validator (amount/date)
- 저장 형식 결정
    - [x] **1차 저장: CSV**

## 2단계: 환경 & 설정 정리 (Day 1 오후)

- [x] `config.yaml` 작성
    - base_url, 목록/상세 path, 타임아웃, retry 횟수, 셀렉터 초안
- [x] Playwright 설치 및 브라우저 준비
    - `playwright install`
- [x] 프로젝트 구조 잡기
    - `src/domain`, `src/scraper`, `src/repository`, `src/service`, `src/utils`
- [x] 간단한 로깅 설정 (structlog 또는 logging 한쪽 선택)
    

## 3단계: 크롤링 루프 MVP (Day 2)

- [x] 목록 페이지 → 상세 페이지 진입 코드
  - [x] BrowserController : 브라우저 세션이 선행 조건이므로 먼저 안정화
  - [x] Parser : 파서로 스키마 적합성 확인 후 저장/서비스 재작업을 최소화
  - [x] Repository : 저장소는 파서 출력 확정 후 구현해야 CSV 컬럼/정규화가 안정적
  - [x] Service : 서비스는 구성 요소가 준비된 뒤 연결해야 흐름 검증이 쉬움
- [x] HTML/API 응답 가져와서 핵심 필드 추출
- [x] 최소 1페이지(몇 개 공고) CSV에 저장까지 확인: Pydantic 모델/파서가 실제 응답과 잘 맞는지 검증
        

## 4단계: 안정성 기능 추가 (Day 3)

- [x] tenacity 재시도: 가장 빈번한 실패(네트워크/타임아웃)를 먼저 줄이기
    - [x] 네트워크/타임아웃에 대해 3회 retry
- [x] 체크포인트 저장/재시작 : 중단 복구의 핵심이므로 MVP 검증 후 바로 추가
    - [x] 마지막 페이지/공고 ID를 파일에 저장하고 재시작 시 사용
- [x] 중복 방지 : 저장소/체크포인트 설계가 확정된 뒤 적용하는 게 안전
    - CSV 기준 `bid_pbanc_no` + `bid_pbanc_ord` 중복 스킵
    - in-memory set는 **옵션**으로 구현하거나 README에 제안만 해도 충분

### 추가 개선 계획 (4~5단계 공통)
- [ ] 상세 하위 리스트/맵 CSV 저장 확장
    - bidPbancItemlist, bidLmtRgnList, bidLmtIntpList, dmLcnsLmtPrmsIntpList,
      rbidList, bdngCrstList, bidPstmNomnEtpsList, bidInfoList, bsamtMap
- [ ] 개찰결과 실데이터 더 확보
    - 결과가 존재하는 페이지 범위 확대 테스트 및 저장 확인
- [ ] 필드 정규화 보완
    - 숫자/날짜 포맷 다양성 추가 대응(상세 리스트에도 적용)
- [ ] (선택) 구조화 로그
    - “가능하면” 요구 충족을 위해 structlog 전환 고려
        

## 5단계: 운영 모드 & 로그 (Day 4)

- [x] CLI 모드 확장 : 실행 모드가 확정되어야  로그에 필요한 이벤트 범위가 결정됨
    - once, resume, interval(혹은 cron에서 쉽게 돌릴 수 있게 인자 설계)
    - Click이면 좋고, 시간이 빠듯하면 argparse도 충분
- [ ] 로그 구조화 : 안정성 확보 후 로그를 확장해야 의미 없는 로그가 줄어듦
    - 최소한: 시작/종료, 페이지 이동, 저장 성공/실패, 스킵 사유
    - 나중에 log를 읽고 “무슨 일이 있었는지 5분 안에 설명 가능”하게
        

## 6단계: 문서 & 테스트 & 마무리 (Day 5)

- README 작성
    - 실행 방법, config 설명, 설계 의도, 트레이드오프, 한계, 개선 아이디어
- 테스트
    - [x] Pydantic 모델(validator), 파서 함수에 대해 pytest 몇 개
    - 여유 있으면 서비스 레벨의 간단한 통합 테스트
- 최종 점검
    - Ctrl+C 후 resume 확인
    - 다른 디렉터리에서 새 venv로 README만 보고 돌아가는지 테스트
        


## readme 구성 계획
>  1_troubleshooting: 날짜별 이슈/해결 기록과 2_decision_log: 기술 선택 이유 기록를 쌓으며 개발하고 최종적으론 선별해 readme를 구성
- Introduction: 프로젝트 목적/가치 + 한 줄 요약
- Tech Decisions: Python/Playwright(or Selenium)/SQLite(or CSV) 선택 이유
- Core Engineering: 재시도(tenacity), 체크포인트, 중복 방지, 예외 격리
- Troubleshooting: 실제 케이스 2~3개 요약
- How to Run: 재현 가능한 명령어(설정/의존성/출력)
- Future Works: 병렬화, 알림, 모니터링, 성능 개선

## 결정 보류/추후 반영(상세 메모)
### 3.0. 크롤링 조합 비교: Ferrari vs Tank

**1) The Ferrari Stack**
- Playwright (목록/로그인) + httpx (상세 비동기 요청) + Selectolax (초고속 파싱)
- **장점:** 압도적인 속도. 브라우저 렌더링 없이 상세 페이지를 비동기로 수집하므로 대량 처리에 유리.
- **치명적 리스크:** 세션(Cookie/Header) 동기화. WAF/지문(Fingerprint) 검사 시 httpx가 차단될 수 있어, 안정성 확보에 예상치 못한 시간이 소모될 위험.

**2) The Tank Stack (후보)**
- Playwright (모든 탐색/요청) + Selectolax(또는 BeautifulSoup)
- **후보 이유:**
  - 세션 관리 불필요: 브라우저가 쿠키/세션을 일관되게 유지.
  - 구현 속도: “목록 → 상세 → page.content() → 파싱”의 직관적인 흐름.
  - 안정성 우선: 과제 기준(수백~수천 건)에서는 안정성이 성능보다 중요.
  - 성능 보완: Playwright Async로 탭/컨텍스트 병렬화가 가능하여 현실적인 처리량 확보.

### 3.2. 브라우저 제어: Selenium vs Playwright

* Selenium: 레거시 표준이나, `WebDriver` 버전 관리의 번거로움과 명시적 대기(Explicit Wait) 처리의 복잡성이 존재.
* Playwright: 최신 웹 표준을 준수하며, 네트워크 요청 가로채기(Interception) 및 비동기(Async) 처리에 최적화됨. 특히 M1/M2 Mac 환경에서의 호환성이 우수.

### 3.3. 파싱 전략: BeautifulSoup vs Selectolax vs httpx 혼합

* BeautifulSoup: 사용은 쉬우나 대량 데이터 처리 시 속도 저하.
* Playwright + httpx: 속도는 가장 빠르나, 동적 페이지의 세션(Cookie/Auth) 동기화 과정에서 발생할 수 있는 잠재적 보안 이슈(WAF 차단 등) 리스크 존재.
* Playwright + Selectolax: 브라우저가 세션을 관리하므로 차단 리스크는 최소화하면서, 파싱 단계에서의 병목을 Selectolax로 해결하는 '안정성 중심의 고성능' 전략.

### 3.4. 재현성/로깅/병렬화 (보류 메모)

* Docker 컨테이너 환경을 구성하여, OS나 로컬 환경에 구애받지 않고 `docker-compose up` 명령어로 즉시 실행 가능한 환경 제공.
* 표준 로깅 포맷과 레벨링을 적용하여 장애 원인과 수집 진행 상황을 추적 가능하도록 설계.
* 핵심 이벤트(페이지 이동, 추출 성공/실패, 재시도)를 구조화된 로그로 남겨 재현성을 강화.
* Playwright Async로 탭/컨텍스트 병렬화가 가능하여 현실적인 처리량 확보.
