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
