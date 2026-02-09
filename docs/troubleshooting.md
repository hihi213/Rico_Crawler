# 트러블슈팅

- (작성 전) 발생한 이슈/증상/원인/해결을 간단히 기록
# Troubleshooting Log

## 2026-02-09: 첨부 등록일 파싱 실패

### 증상
- 첨부 메타 저장 시 `AttachmentItem.inpt_dt` 파싱 실패
- 로그에 `invalid date separator` 발생

### 원인
- 첨부 API 응답의 등록일 포맷이 `YYYY/MM/DD HH:mm:ss` 형태
- 기존 파서가 하이픈 포맷만 허용

### 해결
- `AttachmentItem.inpt_dt`에 공통 datetime 파서 적용
- 첨부 CSV 저장 재실행 후 정상 저장 확인

## 2026-02-09: 개찰 점수 필드 타입 불일치

### 증상
- `BidOpeningResult` 저장 시 점수 필드 타입 오류로 스킵 발생

### 원인
- `ibx_evl_scr_prpl/prce/ovrl`이 숫자(0)로 내려오는 케이스 존재
- 모델이 문자열만 허용해 검증 실패

### 해결
- 점수 필드를 문자열로 정규화하는 validator 추가
- 2페이지 재수집 결과 `bid_opening_result.csv` 생성 확인

## 2026-02-09: 페이지 크기 100건 확대 영향

### 증상
- 2페이지 수집 시 레코드 수가 대폭 증가

### 원인
- `recordCountPerPage`를 100으로 설정해 페이지당 수집량 증가

### 해결
- 정상 동작 확인: 2페이지 기준 목록/상세 200건, 첨부/공지/개찰 요약/결과 저장 완료
