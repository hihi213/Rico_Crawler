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
