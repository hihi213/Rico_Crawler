# 기술 스택 선정 및 아키텍처 설계 (Architecture Decision Records)

## 1. 개요 및 의사결정 배경

본 프로젝트의 핵심 목표는 "제한된 시간 내에, 누리장터의 동적 입찰 정보를 '제품 수준(Product-Level)'의 안정성을 갖춰 수집하는 시스템을 구축"하는 것입니다.

초기에는 리코(RiCO)의 주력 기술 스택인 Spring Boot(Java)를 고려하였으나, 과제의 요구사항인 '동적 크롤링의 안정성'과 '완성도(견고함, 재현성)'를 최우선 순위로 두어 Python 생태계의 강점을 활용하되, 엔터프라이즈 백엔드 아키텍처를 적용하는 전략을 채택했습니다.

## 2. 최종 기술 스택 (Tech Stack)

| 구분 | 선택 기술 | 선정 이유 |
| --- | --- | --- |
| Language | Python 3.14.3 | 풍부한 크롤링 라이브러리 생태계 및 빠른 프로토타이핑 지원. (단, Type Hinting을 엄격히 적용하여 안정성 확보) |
| Browser Control | Playwright | Selenium 대비 빠른 실행 속도, 안정적인 Auto-wait 기능, 브라우저 바이너리 관리의 용이성을 위해 선택. |
| Parsing | Selectolax | 대량의 DOM 탐색 시 BeautifulSoup 대비 압도적인 파싱 속도(Low-level C binding) 제공. |
| Validation | Pydantic | 수집 데이터의 무결성 보장을 위해 Java의 Entity/DTO 검증 로직과 유사한 런타임 타입 검증 구현. |
| Persistence | SQLite | 별도의 DB 설치 없이 로컬 파일 기반으로 상태(State)를 저장하고, 중단 시 이어하기(Resumability) 기능을 구현하기 위함. |

## 3. 대안 비교 및 트레이드오프 (Trade-off Analysis)

기술 선정 과정에서 검토했던 대안들과 최종 선택의 논리는 다음과 같습니다.

### 3.1. 언어 선택: Java(Spring Boot) vs Python

* 고려 사항: 리코의 실무 환경인 Spring Boot/JPA 적응력 어필 vs 과제 기한 내 완성도.
* 판단: Java는 정적 타입 언어로서의 안정성은 높으나, 크롤링 환경 설정 및 보일러플레이트 코드로 인한 오버헤드가 큼.
* 결정: Python을 선택하되, 백엔드 아키텍처 원칙(계층 분리, 타입 명시)을 적용하여 생산성과 구조적 안정성을 동시에 확보함.

## 4. 아키텍처 설계 원칙 (Engineering Principles)

본 프로젝트는 단순한 스크립트(`script.py`)가 아닌, 확장 가능한 애플리케이션으로 설계되었습니다.

1. Layered Architecture (계층형 구조):
* Spring MVC 패턴을 차용하여 역할과 책임을 명확히 분리했습니다.
* `Controller`: 실행 흐름 제어 및 CLI 인자 처리.
* `Service`: 크롤링 비즈니스 로직, 재시도(Retry), 에러 핸들링.
* `Repository`: 데이터 저장 및 중복 방지(Unique Check).
* `Domain`: Pydantic을 활용한 엄격한 데이터 스키마 정의.


2. Robustness (견고함):
* Resumability: 크롤링 상태(마지막 페이지, 날짜)를 SQLite에 기록하여, 비정상 종료 후 재실행 시 해당 지점부터 재개.
* Data Integrity: Pydantic Validator를 통해 금액(`String` -> `Int`), 날짜 포맷 등을 정규화하여 저장.


3. Reproducibility (재현성):
* Docker 컨테이너 환경을 구성하여, OS나 로컬 환경에 구애받지 않고 `docker-compose up` 명령어로 즉시 실행 가능한 환경 제공.

4. Observability (관찰 가능성):
* 표준 로깅 포맷과 레벨링을 적용하여 장애 원인과 수집 진행 상황을 추적 가능하도록 설계합니다.
* 핵심 이벤트(페이지 이동, 추출 성공/실패, 재시도)를 구조화된 로그로 남겨 재현성을 강화합니다.

5. Extensibility (확장성):
* 스키마 변경, 필드 추가, 수집 범위 확장을 대비해 Parser/Extractor를 모듈화합니다.
* 저장소 계층 분리로 SQLite → RDBMS 전환 시 영향 범위를 최소화합니다.

## 정규화 규칙 기준 정리

### 결정
- 날짜/시간은 `datetime`으로 표준화 (`YYYY/MM/DD HH:mm`, `YYYY/MM/DD HH:mm:ss`)
- 금액은 콤마 제거 후 `int`, 빈 값은 `null`
- Y/N 플래그는 `bool` 변환 (`Y`/`N` 외는 `null`)
- 코드/코드명은 쌍으로 저장
- 사업자등록번호는 하이픈 제거 저장, 표시용은 원문 유지 가능
- 문서번호는 공백/탭 제거 후 저장

### 이유(실무 기준)
- 검색/필터/통계를 안정적으로 수행하기 위해 타입과 포맷을 일관화
- 동일 의미 값의 비교/중복 판단 정확도 향상
- 불명확한 값은 `null`로 두어 오류 전파를 방지
- 표시용 원문 보존으로 사용자 표기 요구를 충족

### 진행 과정
1) 목록/상세 공통으로 사용하는 필드 중 비교/집계에 영향을 주는 항목 선정
2) 값의 의미가 바뀌지 않는 범위에서 최소 변환(포맷/구분자 제거)만 적용
3) 불명확/누락 값은 `null` 처리로 다운스트림 안정성 확보

## 관계 정의 흐름 정리

### 결정
- 목록(BidNoticeListItem) 1 ---- n 상세(BidNoticeDetail) 관계는 `bid_pbanc_no` + `bid_pbanc_ord`로 연결
- 상세 1 ---- n 첨부(AttachmentItem)는 `unty_atch_file_no`로 연결
- 상세 1 ---- n 개찰결과(BidOpeningResult)는 `bid_pbanc_no` + `bid_pbanc_ord` + `bid_clsf_no` + `bid_prgrs_ord`로 연결

### 근거
> 단일 객체(Map/Object)로 오는건 1:1관계이고, (List/Array)로 오는건 1:N관계이다.
- 목록 응답의 식별 키가 상세 요청 키로 그대로 사용됨
- 상세 응답의 `untyAtchFileNo`가 첨부 목록 요청 키로 사용됨
- 개찰결과 요청 키가 상세 식별자와 동일한 조합으로 구성됨

## 테스트 기준 설정 이유

### 결정
- 스키마 샘플 최소 5건 확보(목록 3, 상세 2 이상)
- 필수 필드 누락/포맷 오류에 대한 validator 테스트
- 날짜/금액/플래그 정규화 케이스 테스트

### 이유(실무 관점)
- 최소 샘플 수를 확보하면 규칙 변경 시 회귀 여부를 빠르게 판단 가능
- 필수 필드 검증은 데이터 품질과 저장 안정성에 직결
- 정규화 테스트는 비교/필터/집계의 신뢰성을 보장

## 공통 키 모델 및 공통 필드 분리

### 결정
- `BidNoticeKey`를 목록/상세/개찰결과 공통 식별자 모델로 고정
- 목록행/상세 공통 필드를 별도로 문서화해 중복 정의를 최소화

### 이유(실무 관점)
- 목록/상세/개찰결과가 같은 식별자를 공유하는데, 각 모델에 매번 중복 정의하면 유지보수가 어려워짐
- 동일 키 재사용으로 저장/조회/조인 단순화
- 공통 필드 분리로 모델 확장 시 변경 범위 축소

### 진행 과정
1) 목록행, `bidPbancMap`, `pbancOrgMap`의 공통 필드를 교집합으로 정리
2) 목록 전용/상세 전용 필드를 분리하여 스키마에 명시

## 도메인 모델 스켈레톤 확정

### 결정
- 목록/상세/개찰/첨부를 별도 Pydantic 모델로 분리
- 공통 식별자는 `BidNoticeKey`로 상속해 일관성 유지

### 이유(실무 관점)
- 소스(API)가 다른 데이터를 한 모델로 합치면 검증/저장 오류가 증가
- 공통 키 상속으로 조인/중복방지/재시작 로직이 단순해짐

### 진행 과정
1) `BidNoticeListItem`, `BidNoticeDetail`, `BidOpeningSummary`, `BidOpeningResult`, `AttachmentItem` 생성
2) `BidNoticeKey`를 상속해 공통 식별자 통일

## 정규화 validator 적용

### 결정
- 날짜/시간, 금액, Y/N 플래그, 문서번호, 사업자등록번호를 모델 레벨에서 정규화
- Pydantic v1/v2 모두 동작하도록 validator 헬퍼를 도입

### 이유(실무 관점)
- 파싱 단계에서 정규화를 고정하면 저장/조회/집계의 안정성이 높아짐
- 런타임 환경 차이(Pydantic 버전)로 인한 오류를 예방

### 진행 과정
1) `_parse_datetime`, `_parse_int`, `_parse_bool_yn`, `_normalize_doc_no`, `_normalize_biz_reg_no` 구현
2) 목록/상세/개찰/첨부/코드 모델에 필드별 validator 적용

## CommCode 코드 사전 최소 스키마 확정

### 결정
- `code_group`, `code`, `code_nm`, `use_yn` 4필드만 우선 확정
- UNIQUE(`code_group`, `code`) 키 제약을 권장

### 이유(실무 관점)
- 코드/코드명은 거의 모든 화면 필터·라벨에 쓰이므로 별도 사전 테이블이 필요
- 코드 조회/필터링에 필요한 최소 단위만 고정해 범위 과대화를 방지
- 그룹-코드 조합 고유성으로 중복 저장 및 조회 오류 예방

### 진행 과정
1) 실제 화면/응답의 코드-코드명 쌍 저장 요구에 맞춰 최소 컬럼 정의
2) 확장 가능성을 열어 두고 필수 제약만 우선 명시

## 미확정 항목 트래킹 표 운영

### 결정
- `target/status/sample_id/note` 4컬럼으로 미확정 항목 추적
- 상태는 `pending/verified/removed`로 고정

### 이유(실무 관점)
- 샘플이 더 필요하거나 확인되지 않은 필드를 문서로만 두면 누락되기 쉬움.
- 샘플 확보 진행상황을 명시적으로 관리해 누락/중복 확인을 방지
- 추후 검증 근거와 결론을 빠르게 공유 가능

### 진행 과정
1) 2.1.2 미확정 항목을 트래킹 대상으로 지정
2) 표 형태로 최소 정보를 기록하도록 스키마에 추가

## 개찰결과 모델 분리(요약/목록)

### 결정
- `BidOpeningSummary(pbancMap)`와 `BidOpeningResult(oobsRsltList)`를 분리 정의
- 연결키는 `bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`로 고정

### 이유(실무 관점)
- 개찰결과 API는 pbancMap(단일 요약)과 oobsRsltList(리스트 결과)가 구조적으로 다름.
- 요약(map)과 목록(list) 구조 차이를 명확히 분리해 파싱/저장 오류를 줄임
- 동일 키로 상세/개찰결과 조인을 안정화

### 진행 과정
1) 개찰결과 API의 `pbancMap`/`oobsRsltList` 필드 구조를 분리
2) 핵심 필드와 선택 필드를 분리해 스키마에 반영

## 현재 폴더 구조 선택

### 결정
- `src/domain`, `src/infrastructure`, `src/service`, `src/core` + `main.py` 구조를 채택
- 실행 흐름은 `main.py( CLI ) -> service -> infrastructure -> domain`으로 고정

### 이유(실무 관점)
- 레이어 분리를 강제해 책임과 테스트 단위를 명확히 하기 위함
- 크롤링/저장/파서 변경이 서로 독립적으로 가능해 유지보수성이 높음
- 과제 평가 기준(모듈화/확장성)에 맞는 구조

### 진행 과정
1) 도메인 모델을 `src/domain`로 분리
2) 브라우저/파서/리포지토리를 `src/infrastructure`로 분리
3) 비즈니스 로직은 `src/service`에 고정
4) 공통 유틸/설정은 `src/core`로 분리

## CSV 1차 저장 형식 확정

### 결정
- 1차 저장은 CSV로 확정
- 1:N 구조는 CSV 파일을 분리 저장
- 컬럼 순서를 고정하여 재현성과 비교 가능성 확보

### 이유(실무 관점)
- SQLite보다 CSV는 구현이 빠르고 결과 검증/제출이 쉬움 (과제 일정 우선)
- 리스트/상세/개찰/첨부는 구조가 달라 단일 파일에 혼합 저장 시 오류 위험 증가
- 컬럼 순서 고정으로 스키마 변경 시 차이 추적과 회귀 비교가 쉬움

### 진행 과정
1) 도메인 모델 기준으로 파일 단위를 분리
2) 핵심 키 → 상태/분류 → 일정 → 메타 순으로 컬럼 순서 정의

## 로깅 방식 선택

### 결정
- structlog 대신 표준 `logging`을 1차로 사용
- 추후 필요 시 structlog로 전환하기 쉽도록 logger 호출부를 표준화해 구현
- 포맷은 `%(asctime)s %(levelname)s %(name)s %(message)s`로 고정

### 이유(실무 관점)
- structlog는 JSON 구조화 로그에 강해 모니터링/필터링/분석(ELK 등) 연동이 쉽지만,
- 1차 구현에서는 로그 요구사항이 단순하므로 표준 logging으로도 충분함
- logger 호출부를 표준화해두면 structlog 전환 시 변경 범위를 최소화할 수 있음
- 외부 의존성 추가 없이 바로 사용 가능해 초기 구현 속도가 빠름

## BrowserController 초기화 방식

### 결정
- Playwright 컨텍스트에 기본 timeout과 user agent를 설정
- 컨텍스트를 생성/종료하는 책임을 BrowserController에 집중

### 이유(실무 관점)
- 기본 timeout을 컨텍스트에 두면 파서/서비스에서 대기 정책을 일관되게 적용 가능
- UA를 중앙에서 관리하면 환경 차이에 따른 접근 실패를 줄일 수 있음
- 컨텍스트 라이프사이클을 한 곳에 모아 자원 누수를 예방

## Parser 목록 파싱 방식

### 결정
- 목록 그리드는 `td[col_id]` 기반으로 일괄 수집
- 파서 반환은 원본 맵(list[dict]) 형태로 유지

### 이유(실무 관점)
- `col_id`가 API 필드와 1:1 매핑되어 셀렉터 수를 최소화할 수 있음
- 원본 맵을 서비스에서 검증/정규화하면 누락 필드에도 유연하게 대응 가능

## Repository CSV 저장 방식

### 결정
- CSV 저장 경로는 `sqlite_path`의 parent 디렉터리를 사용
- 컬럼 순서는 도메인 모델 필드 순서를 그대로 고정
- append 모드로 누적 저장

### 이유(실무 관점)
- 설정을 하나로 유지하면서도 CSV/SQLite 전환에 유연하게 대응 가능
- 컬럼 순서 고정으로 스키마 비교/회귀 검증이 쉬움
- 중단 후 재실행 시 결과를 보존하기 위해 append가 적합

## 목록 마감일 필드 Optional 처리 (2026-02-09)

### 결정
- `BidNoticeListItem.slpr_rcpt_ddln_dt`를 Optional로 완화

### 이유(실무 관점)
- 실제 목록 API 응답에서 `slprRcptDdlnDt`가 null로 내려오는 케이스가 확인됨
- 공고 상태/유형에 따라 마감일이 미확정일 수 있어 필수로 강제하면 검증 실패가 발생

### 진행 과정
1) 목록 API 1페이지 수집 중 `slprRcptDdlnDt=null` 케이스 확인
2) 스키마/모델 불일치 판단 후 Optional로 조정

## 목록 수집을 API 직호출로 전환 (2026-02-09)

### 결정
- 목록 페이지 DOM 크롤링 대신 `selectBidPbancList.do` API를 직접 호출
- `dlParamM` payload 및 필수 헤더(Menu-Info/Target-Id 등)를 설정으로 고정

### 이유(실무 관점)
- UI 그리드가 초기 로드에서 데이터가 비어 있고 검색 버튼이 숨김 처리되어 자동화 실패
- API 호출이 가장 안정적이며 재시도/페이징 제어가 명확함

### 진행 과정
1) 네트워크 탭에서 `dlParamM` payload와 헤더를 캡처
2) `config.yaml`에 payload/headers 템플릿 추가
3) Service에서 API 호출 경로를 우선 사용하도록 분기

## 체크포인트 JSON 저장 (2026-02-09)

### 결정
- 체크포인트를 `data/checkpoint.json`에 원자적으로 저장
- 저장 시점은 페이지 처리 직후, 재시작은 `current_page` 기준

### 이유(실무 관점)
- 간단한 파일 기반 체크포인트가 구현/복구가 빠름
- 원자적 교체로 중간 파일 손상 방지

### 진행 과정
1) `CheckpointStore`로 저장/로드 구현
2) Service에서 시작 페이지 로드 및 페이지별 저장 연동

## CSV 기반 중복 방지 (2026-02-09)

### 결정
- 목록: `bid_pbanc_no + bid_pbanc_ord`
- 상세: `bid_pbanc_no + bid_pbanc_ord + bid_clsf_no + bid_prgrs_ord`
- 기존 CSV에서 키를 로드해 중복을 스킵

### 이유(실무 관점)
- SQLite 전환 전 단계에서 빠른 중복 방지 필요
- 재실행 시 중복 적재 방지

### 진행 과정
1) CSV 로드 시 키 캐시 구성
2) 저장 전 중복 필터링 적용

## tenacity 재시도 적용 (2026-02-09)

### 결정
- 목록 API 호출과 상세 팝업 응답에 tenacity 재시도 적용

### 이유(실무 관점)
- 네트워크/일시 오류로 인한 실패를 자동 복구
- 실패 항목은 스킵 로그로 남겨 전체 수집을 유지

### 진행 과정
1) 목록 API 호출에 retry wrapper 적용
2) 상세 팝업 호출에도 동일한 retry 정책 적용

## 첨부/공지/개찰 CSV 저장 확장 (2026-02-09)

### 결정
- 공지/첨부/개찰요약/개찰결과를 별도 CSV로 분리 저장
- 첨부 `inpt_dt`는 목록/상세와 동일 포맷 파서로 정규화

### 이유(실무 관점)
- 1:N 구조를 분리해 저장해야 데이터 정합성과 조회가 안정적임
- 첨부 등록일이 `YYYY/MM/DD HH:mm:ss` 형식으로 내려와 파서 보완이 필요

### 진행 과정
1) Repository에 `bid_notice_noce.csv`, `bid_notice_attachment.csv`, `bid_opening_summary.csv`, `bid_opening_result.csv` 추가
2) Service에서 수집된 공지/첨부/개찰 데이터를 저장으로 연결
3) AttachmentItem `inpt_dt` 정규화 validator 추가

## Service 목록 변환/저장 책임 분리

### 결정
- Parser는 원본 추출만 담당하고, Service에서 도메인 모델 변환을 수행
- camelCase(col_id) → snake_case 도메인 매핑은 Service에서 명시적으로 정의
- 페이지네이션은 `pagination_next` 셀렉터가 있을 때만 진행

### 이유(실무 관점)
- 추출(파서)과 검증/정규화(도메인) 경계를 명확히 해 유지보수성을 높임
- 매핑 로직을 한 곳에 모아 필드 변경 시 영향 범위를 줄임
- 셀렉터 미존재 상황에서 무한 대기/오작동을 방지
