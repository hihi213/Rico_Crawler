# 스키마 정의 (누리장터 입찰공고)

## 빠른 목차
- A. API/흐름/관찰
- B. 도메인 엔티티
- C. 정규화/중복/관계/테스트
- D. 보완 항목/트래킹

## A. API/흐름/관찰

## 1. 개요
- 소스: 누리장터 입찰공고 목록 API/그리드 (목록 JSON 기준)
- 식별자: `bid_pbanc_no` + `bid_pbanc_ord` 조합이 고유 키
- 정규화: 날짜/시간, 코드/코드명 분리 저장
- 참고: 목록에서 상세 클릭 시 URL이 유지됨 → 상세는 별도 API/요청 규격 확인 필요

## 1.1 목록 HTML/XHR 기반 추론 근거
- 그리드 HTML `col_id`가 JSON 필드명과 1:1로 대응됨 → UI 라벨과 API 필드 매핑 확정
- XHR/Fetch에서 `dlParamM` 요청 구조와 응답 envelope(`result`, `ErrorMsg`, `ErrorCode`) 확인
- 페이징 제어는 `currentPage`, `recordCountPerPage` 기반, 전체 건수는 `totCnt`
- 날짜 포맷은 `YYYY/MM/DD HH:mm`, 플래그는 Y/N 문자열
- 목록 상세 클릭 시 URL이 유지됨 → 상세는 화면 전환이 아니라 별도 API 호출로 추정

## 2. 목록 API 스키마
### 엔드포인트
- URL: `https://nuri.g2b.go.kr/nn/nnb/nnba/selectBidPbancList.do`
- Method: `POST`
 
### 요청(payload) `dlParamM`
- `bidPbancNo` (str): 입찰공고번호 검색
- `bidPbancOrd` (str): 차수 검색
- `bidPbancNm` (str): 입찰공고명 검색
- `prcmBsneSeCd` (str): 공고분류 코드
- `bidPbancPgstCd` (str): 공고게시 코드
- `bidMthdCd` (str): 입찰방식 코드
- `pbancPstgStDt` (str): 공고게시 시작일(YYYYMMDD)
- `pbancPstgEdDt` (str): 공고게시 종료일(YYYYMMDD)
- `onbsPrnmntStDt` (str): 개찰 시작일(YYYYMMDD)
- `onbsPrnmntEdDt` (str): 개찰 종료일(YYYYMMDD)
- `recordCountPerPage` (str): 페이지 크기
- `rowNum` (str): 행 번호(옵션)
- `kbrdrId` (str): 사용자 ID(옵션)
- `pbancInstUntyGrpNo` (str): 기관 식별자(옵션)
- `pdngYn` (str): 보류 여부(옵션)
- `currentPage` (int): 현재 페이지
- `pbancSttsCd` (str): 공고구분 코드
- `pbancKndCd` (str): 공고종류 코드
- `stdCtrtMthdCd` (str): 계약방법 코드
- `scsbdMthdCd` (str): 낙찰방법 코드
- `untyGrpNo` (str): 통합그룹 번호(옵션)
- `usrTyCd` (str): 사용자 유형(옵션)
- `pbancPstgYn` (str): 게시 여부(Y/N)
- `frgnrRprsvYn` (str): 외국인대표 여부(옵션)

### 페이징 규칙 [확정]
- 페이지 이동은 `currentPage`만 변경됨 (예: 1 → 2)
- 나머지 필터/기간 파라미터는 동일하게 유지됨

## 2.1.6 UI 실제 플로우(보정)
### 검색 화면 진입
- 홈 진입 → 팝업 닫기
- 상단 메뉴에서 “입찰공고”에 마우스 오버
- 하단에 나타나는 “입찰공고목록” 클릭
- 검색 화면으로 전환
- 조건 선택 후 “검색” 클릭 → 검색 목록 표시

### 목록 → 상세
- 목록에서 “입찰공고명” 클릭 → 입찰공고 상세 **팝업** 표시

### 목록 → 개찰결과 → 상세
- 목록에서 “개찰결과” 클릭 → 개찰결과 **화면 전환**
- 개찰결과 화면에서 “공고상세” 클릭 → 입찰공고 상세 **팝업** 표시

## 2.1.7 UI DOM 셀렉터(검색/목록)
### 메뉴 진입
- 상단 “입찰공고” 1뎁스(hover): `#mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_btn_menuLvl1`
- 하단 “입찰공고목록” 3뎁스(click): `#mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3`

### 검색 조건(기본)
- 검색 영역: `#mf_wfm_container_grpSrchBox`
- 입찰공고번호: `#mf_wfm_container_tbxBidPbancNo`
- 입찰공고명: `#mf_wfm_container_tbxBidPbancNm`
- 공고분류: `#mf_wfm_container_sbxBsneClsf`
- 진행상태: `#mf_wfm_container_sbxPrgrsStts`
- 공고구분: `#mf_wfm_container_sbxBidPbancMth`
- 공고종류: `#mf_wfm_container_tbxPbancKndCd`
- 계약방법: `#mf_wfm_container_tbxStdCtrtMthdCd`
- 낙찰방법: `#mf_wfm_container_tbxScsbdMthdCd1`
- 검색 버튼: `#mf_wfm_container_btnS0001`
- 초기화 버튼: `#mf_wfm_container_btnIntz`

### 검색 조건(개찰일자 모드)
- 개찰 조건 영역(숨김/토글): `#mf_wfm_container_grpSrchBox2`
- 개찰일자 검색 버튼: `#mf_wfm_container_btnS0002`
- 개찰일자 초기화 버튼: `#mf_wfm_container_btnIntz2`

### 목록 그리드
- 그리드 컨테이너: `#mf_wfm_container_grdBidPbancList`
- 데이터 tbody: `#mf_wfm_container_grdBidPbancList_body_tbody`
- 입찰공고명 링크(상세 팝업): `#mf_wfm_container_grdBidPbancList_body_tbody td[col_id="bidPbancNm"] a`
- 개찰결과 버튼: `#mf_wfm_container_grdBidPbancList_body_tbody td[col_id="btnOnbsRslt"] button`
- 개찰결과 버튼(활성 조건): disabled 속성 없을 때만 클릭 가능
- 개찰결과 버튼(상태 기준, 관찰): `pbancSttsGridCdNm`이 "개찰완료"일 때 활성화됨

### 페이지네이션
- 페이지 컨테이너: `#mf_wfm_container_pagelist`
- 페이지 번호 버튼: `#mf_wfm_container_pagelist_page_{N}` (예: `#mf_wfm_container_pagelist_page_1`)
- 이전/다음: `#mf_wfm_container_pagelist_prev_btn`, `#mf_wfm_container_pagelist_next_btn`
- 처음/마지막: `#mf_wfm_container_pagelist_prevPage_btn`, `#mf_wfm_container_pagelist_nextPage_btn`

### 개찰결과 화면
- 화면 타이틀: `#mf_wfm_cntsHeader_spnHeaderTitle` (값: "개찰결과조회")
- 공고상세 버튼: `#mf_wfm_container_btnBidPbancP`

### 입찰공고 상세 팝업
- 팝업 최상위 컨테이너: `#mf_wfm_container_BidPbancP`
- 팝업 닫기 버튼: `#mf_wfm_container_BidPbancP_close`

### 셀렉터 안정성 가이드
- 우선순위: 고정 `id` > `col_id` 기반 셀 > `button.w2window_close` 공통 클래스
- 회피 대상: `wq_uuid_*`가 포함된 동적 id (세션마다 변경될 수 있음)

## 2.1.8 개찰결과조회 화면(DOM) 기반 추론 [관찰]
### 화면 특징
- 목록에서 "개찰결과" 버튼 클릭 시 **개찰결과 화면으로 전환**
- 상단 요약(공고일반) + 하단 그리드(개찰결과목록) 구성

### 상단 요약 필드(DOM 라벨 기반)
- 입찰공고번호-차수: `bidPbancNum` (예: `R26BK01292424-001`)
- 문서번호: `docNo` (예: `2026-01호`)
- 계약방법: `stdCtrtMthdCdNm` (예: `일반경쟁`)
- 낙찰방법: `scsbdMthdCdNm` (예: `적격심사제`)
- 민간수요자: `grpNm` (예: `창동주공1단지아파트 재건축추진준비위원회`)
- 실제개찰일시: `onbsDt` (예: `2026/02/06 19:11`)
- 집행관: `executorNm` (예: `이장백`)

### 개찰결과 그리드 컬럼(col_id 기준)
- `ibxOnbsRnkg`: 순위/No
- `ibxBzmnRegNo`: 사업자등록번호
- `ibxGrpNm`: 조달업체명
- `ibxRprsvNm`: 대표자명
- `bidUfnsRsnNm`: 사전판정(예: 정상/서류미제출)
- `ibxEvlScrPrpl`: 제안서 평가점수
- `ibxEvlScrPrce`: 입찰 가격점수
- `ibxEvlScrOvrl`: 총점
- `ibxBdngAmt`: 투찰금액(원)
- `ibxSlprRcptnDt`: 투찰일시
- `bdngCnt`: 참여횟수(링크형 표기)
- `btnFileView`: 첨부/파일보기 버튼
- `sfbrSlctnRsltCd`: 낙찰여부

### 보완 필요
- 실제 API 응답 필드명 확인 필요(현재는 DOM 기반 임시 매핑)

## 2.1.9 개찰결과조회 API [관찰]
### 엔드포인트
- URL: `https://nuri.g2b.go.kr/nn/nnb/nnbd/selectOobsRsltDetl.do`
- Method: `POST`

### 요청(payload) `dlSrchCndtM`
- `bidPbancNo` (str): 입찰공고번호
- `bidPbancOrd` (str): 차수
- `bidClsfNo` (str): 분류 번호
- `bidPrgrsOrd` (str): 진행 차수
- `bidPbancPgstCd` (str): 공고게시 코드(샘플 빈 값)
- `kbrdrId` (str): 사용자 ID(샘플 빈 값)
- `etpsUntyGrpNo` (str): 업체 통합그룹 번호(샘플 빈 값)
- `prcrId` (str): 집행관/담당자 ID(샘플 빈 값)
- `prcsRsn` (str): 처리 사유(샘플 빈 값)
- `cvlnOrbySeCd` (str): 민간수요 구분(샘플 빈 값)
- `cvlnEtpsSrngPgstCd` (str): 민간업체 공고 구분(샘플 빈 값)
- `myBdonLisMovYn` (str): 내 입찰 이동 여부(샘플 빈 값)

### 응답(envelope)
- `result.pbancMap` (dict): 상단 요약 + 공고 메타
- `result.grdLisList` (list): 공고 진행 요약(단건 리스트 형태)
- `result.oobsRsltList` (list): 개찰결과 목록(그리드)
- `ErrorMsg` (str)
- `ErrorCode` (int)

### 응답 필드(샘플 기준)
#### `pbancMap`
- `bidPbancNo`, `bidPbancOrd`, `bidPbancNum`, `bidPbancFullNo`
- `prcmBsneSeCd`, `prcmBsneSeCdNm`
- `bidPbancPgstCd`
- `pbancInstUntyGrpNo`, `pbancInstUntyGrpNoNm` (기관/조합명)
- `bidBlffId`, `bidBlffIdNm` (집행관)
- `edocNo`, `usrDocNoVal` (문서번호)
- `bidPbancNm`
- `bidMthdCd`, `bidMthdCdNm`
- `scsbdMthdCd`, `scsbdMthdCdNm`
- `pbancSttsCd`, `pbancSttsCdNm`
- `stdCtrtMthdCd`, `stdCtrtMthdCdNm`
- `bidClsfNo`, `bidPrgrsOrd`
- `ibxOnbsPrnmntDt` (개찰예정일시)
- `ibxOnbsDt` (실제개찰일시)
- `bidPrceAlpt`, `bidPrplAlpt`
- `prcsRsn`
- `bdwetpsUntyGrpNo`, `bdwetpsUntyGrpNm`
- `rlsYn`, `maxPrgrsYn`

#### `grdLisList` (요약 리스트)
- `bidPbancNo`, `bidPbancOrd`, `bidPrgrsOrd`
- `usrDocNoVal`, `bidPbancNm`
- `slprRcptDdlnDt`, `onbsPrnmntDt`
- `stdCtrtMthdCd`, `stdCtrtMthdCdNm`
- `pbancSttsNm`, `pbancSttsYn`

#### `oobsRsltList` (개찰결과)
- `ibxOnbsRnkg` (순위)
- `bidPbancNo`, `bidPbancOrd`, `bidClsfNo`, `bidPrgrsOrd`
- `etpsUntyGrpNo`
- `ibxGrpNm` (조달업체명)
- `ibxBzmnRegNo` (사업자등록번호, 숫자형)
- `ibxBdngAmt` (투찰금액)
- `ibxSlprRcptnDt` (투찰일시)
- `ibxRprsvNm` (대표자명)
- `bidrPrsnNo`, `bidrPrsnNm` (입찰자)
- `bidUfnsRsnCd`, `bidUfnsRsnNm` (사전판정)
- `ufnsYn`, `ufnsYnLtrs`
- `ibxEvlScrPrpl`, `ibxEvlScrPrce`, `ibxEvlScrOvrl`
- `sfbrSlctnOrd`, `sfbrSlctnRsltCd`

## 2.1 상세 관련 호출 흐름 [관찰]
### 페이지 최초 진입 시
- `https://nuri.g2b.go.kr/websquare/suffix.txt`
- `https://nuri.g2b.go.kr/websquare/serverTime.wq`
- `https://nuri.g2b.go.kr/co/coz/coza/util/getSession.do`
- `https://nuri.g2b.go.kr/fa/faz/fazf/PrtlFtre/selectPrtlFtreMainList.do`

### 메뉴 진입 시 (목록 > 입찰공고 > 입찰공고목록)
- `https://nuri.g2b.go.kr/co/coz/coza/util/getSession.do`
- `https://nuri.g2b.go.kr/co/coa/coaa/MainMenu/selectMenuAtetMatrWhenMenuOpen.do`
- `https://nuri.g2b.go.kr/co/coa/coaa/MainMenu/selectMenuAtetMatrBySqno.do`
- `https://nuri.g2b.go.kr/co/cob/coba/CommCd/selectCommCdList.do`

### 검색 클릭 시
- `https://nuri.g2b.go.kr/nn/nnb/nnba/selectBidPbancList.do`

### 목록 행 클릭(상세 진입) 시
- `https://nuri.g2b.go.kr/co/coz/coza/util/getSession.do`
- `https://nuri.g2b.go.kr/co/cob/coba/CommCd/selectCommCdList.do`
- `https://nuri.g2b.go.kr/nn/nnb/nnbb/selectBidPbancPrgsDetl.do`
- `https://nuri.g2b.go.kr/kupload/config/raonkupload.config.txt`
- `https://nuri.g2b.go.kr/fs/fsc/fsca/fileUpload.do`
- `https://nuri.g2b.go.kr/co/cob/coba/CommCd/selectCommCdList.do`
- `https://nuri.g2b.go.kr/nn/nnb/nnbb/selectBidNoceDetl.do`
- `https://nuri.g2b.go.kr/fs/fsc/fscb/UntyAtchFile/selectUntyAtchFileList.do`
- `https://nuri.g2b.go.kr/fs/fsc/fsca/fileUpload.do`

### URL 유지 관련 메모
- 목록/상세 전환에도 브라우저 URL은 유지됨 → 화면 전환이 아닌 API 호출 기반

## B. 도메인 엔티티
## 3. 엔티티: BidNoticeListItem (목록 기준)
### 필수 필드
- `bid_pbanc_no` (str): 입찰공고번호(예: R26BK01322795)
- `bid_pbanc_ord` (str): 차수(예: 000)
- `bid_pbanc_nm` (str): 입찰공고명
- `bid_pbanc_num` (str): 표시용 공고번호-차수(예: `R26BK01292424-001`)
- `pbanc_stts_cd` (str): 공고구분 코드
- `pbanc_stts_cd_nm` (str): 공고구분명(등록공고/변경공고 등)
- `prcm_bsne_se_cd` (str): 공고분류 코드
- `prcm_bsne_se_cd_nm` (str): 공고분류명(공사/용역 등)
- `bid_mthd_cd` (str): 입찰방식 코드
- `bid_mthd_cd_nm` (str): 입찰방식명
- `std_ctrt_mthd_cd` (str): 계약방법 코드
- `std_ctrt_mthd_cd_nm` (str): 계약방법명
- `scsbd_mthd_cd` (str): 낙찰방법 코드
- `scsbd_mthd_cd_nm` (str): 낙찰방법명
- `pbanc_pstg_dt` (datetime): 공고게시일시
- `pbanc_knd_cd` (str): 공고종류 코드
- `pbanc_knd_cd_nm` (str): 공고종류명
- `grp_nm` (str): 기관명/조합명
- `slpr_rcpt_ddln_dt` (datetime): 입찰마감일시
- `pbanc_stts_grid_cd_nm` (str): 진행상태(입찰개시 등)
 - `row_num` (int): 화면 행 번호
 - `tot_cnt` (int): 전체 건수
 - `current_page` (int): 현재 페이지
 - `record_count_per_page` (int): 페이지 크기
 - `next_row_yn` (str): 다음 행 존재 여부(Y/N)

### 선택 필드
- `edoc_no` (str|null): 전자문서번호/공고문 번호
- `usr_doc_no_val` (str|null): 사용자 문서번호
- `pbanc_inst_unty_grp_no` (str|null): 기관 식별자
- `pbanc_pstg_yn` (str|null): 게시 여부(Y/N)
- `pbanc_dscr_trgt_yn` (str|null): 공개대상 여부
- `slpr_rcpt_bgng_yn` (str|null): 접수시작 여부
- `slpr_rcpt_ddln_yn` (str|null): 접수마감 여부
- `onbs_prnmnt_yn` (str|null): 개찰 관련 여부
- `bid_qlfc_end_yn` (str|null): 자격 심사 종료 여부
- `pbanc_bfss_yn` (str|null): 사전공고 여부
- `bid_clsf_no` (str|null): 분류 번호
- `bid_prgrs_ord` (str|null): 진행 차수
- `bid_pbanc_pgst_cd` (str|null): 공고게시 코드
- `sfbr_slctn_ord` (str|null): 낙찰자선정 차수
- `sfbr_slctn_rslt_cd` (str|null): 낙찰자선정 결과 코드
- `doc_sbmsn_ddln_dt` (datetime|null): 문서제출 마감일시
- `cvln_qlem_crtr_no` (str|null): 적격심사 기준 번호
- `cvln_qlem_pgst_cd` (str|null): 적격심사 게시 코드
- `objtdmd_term_dt` (datetime|null): 이의신청 기간
- `bdng_amt_yn_nm` (str|null): 투찰금액 여부 표시(화면 표기용)
- `slpr_rcpt_ddln_dt1` (datetime|null): 추가 마감일시(화면 표기용)

### 포맷 규칙(공고 번호)
- 표시용(화면/그리드): `bidPbancNum = bidPbancNo + "-" + bidPbancOrd` (예: `R26BK01292424-001`)
- 합성키/저장용: `bid_pbanc_no` + `bid_pbanc_ord`를 별도 컬럼으로 유지(고유키)

## 4. 엔티티: BidNoticeDetail (상세 기준, 1차 확정)
### 필수 필드
- 식별자: `bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`
- 공고명: `bid_pbanc_nm`, `bid_pbanc_num`
- 상태: `pbanc_stts_cd`, `pbanc_stts_cd_nm`

### 선택 필드
- 분류/방식: `prcm_bsne_se_cd`, `prcm_bsne_se_cd_nm`, `bid_mthd_cd`, `bid_mthd_cd_nm`,
  `std_ctrt_mthd_cd`, `std_ctrt_mthd_cd_nm`, `scsbd_mthd_cd`, `scsbd_mthd_cd_nm`
- 기관/담당: `pbanc_inst_unty_grp_no`, `pbanc_inst_unty_grp_no_nm`, `grp_nm`,
  `pic_id`, `pic_id_nm`, `bid_blff_id`, `bid_blff_id_nm`, `bsne_tlph_no`, `bsne_fax_no`, `bsne_eml`
- 일정: `pbanc_pstg_dt`, `slpr_rcpt_bgng_dt`, `slpr_rcpt_ddln_dt`, `onbs_prnmnt_dt`, `bid_qlfc_reg_dt`
- 주소/장소: `onbs_plac_nm`, `zip`, `base_addr`, `dtl_addr`, `unty_addr`
- 문서/식별: `edoc_no`, `usr_doc_no_val`
- 플래그: `rbid_prms_yn`, `pbanc_pstg_yn`, `rgn_lmt_yn`, `lcns_lmt_yn`, `pnpr_use_yn`, `pnpr_rls_yn`
- 첨부 연계: `unty_atch_file_no`

### JSON 필드명 -> 도메인 필드명 매핑 (상세 핵심)
- `bidPbancNo` -> `bid_pbanc_no`
- `bidPbancOrd` -> `bid_pbanc_ord`
- `bidClsfNo` -> `bid_clsf_no`
- `bidPrgrsOrd` -> `bid_prgrs_ord`
- `bidPbancNm` -> `bid_pbanc_nm`
- `bidPbancNum` -> `bid_pbanc_num`
- `pbancSttsCd` -> `pbanc_stts_cd`
- `pbancSttsCdNm` -> `pbanc_stts_cd_nm`
- `prcmBsneSeCd` -> `prcm_bsne_se_cd`
- `prcmBsneSeCdNm` -> `prcm_bsne_se_cd_nm`
- `bidMthdCd` -> `bid_mthd_cd`
- `bidMthdCdNm` -> `bid_mthd_cd_nm`
- `stdCtrtMthdCd` -> `std_ctrt_mthd_cd`
- `stdCtrtMthdCdNm` -> `std_ctrt_mthd_cd_nm`
- `scsbdMthdCd` -> `scsbd_mthd_cd`
- `scsbdMthdCdNm` -> `scsbd_mthd_cd_nm`
- `pbancInstUntyGrpNo` -> `pbanc_inst_unty_grp_no`
- `pbancInstUntyGrpNoNm` -> `pbanc_inst_unty_grp_no_nm`
- `grpNm` -> `grp_nm`
- `picId` -> `pic_id`
- `picIdNm` -> `pic_id_nm`
- `bidBlffId` -> `bid_blff_id`
- `bidBlffIdNm` -> `bid_blff_id_nm`
- `bsneTlphNo` -> `bsne_tlph_no`
- `bsneFaxNo` -> `bsne_fax_no`
- `bsneEml` -> `bsne_eml`
- `pbancPstgDt` -> `pbanc_pstg_dt`
- `slprRcptBgngDt` -> `slpr_rcpt_bgng_dt`
- `slprRcptDdlnDt` -> `slpr_rcpt_ddln_dt`
- `onbsPrnmntDt` -> `onbs_prnmnt_dt`
- `bidQlfcRegDt` -> `bid_qlfc_reg_dt`
- `onbsPlacNm` -> `onbs_plac_nm`
- `zip` -> `zip`
- `baseAddr` -> `base_addr`
- `dtlAddr` -> `dtl_addr`
- `untyAddr` -> `unty_addr`
- `edocNo` -> `edoc_no`
- `usrDocNoVal` -> `usr_doc_no_val`
- `rbidPrmsYn` -> `rbid_prms_yn`
- `pbancPstgYn` -> `pbanc_pstg_yn`
- `rgnLmtYn` -> `rgn_lmt_yn`
- `lcnsLmtYn` -> `lcns_lmt_yn`
- `pnprUseYn` -> `pnpr_use_yn`
- `pnprRlsYn` -> `pnpr_rls_yn`
- `untyAtchFileNo` -> `unty_atch_file_no`

## 4.1 엔티티: BidOpeningSummary (개찰결과 요약, `pbancMap`)
### 필수 필드
- 식별자: `bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`
- 공고명/번호: `bid_pbanc_nm`, `bid_pbanc_num`
- 상태: `pbanc_stts_cd`, `pbanc_stts_cd_nm`

### 선택 필드
- 분류/방식: `prcm_bsne_se_cd`, `prcm_bsne_se_cd_nm`, `bid_mthd_cd`, `bid_mthd_cd_nm`,
  `std_ctrt_mthd_cd`, `std_ctrt_mthd_cd_nm`, `scsbd_mthd_cd`, `scsbd_mthd_cd_nm`
- 기관/담당: `pbanc_inst_unty_grp_no`, `pbanc_inst_unty_grp_no_nm`, `grp_nm`,
  `bid_blff_id`, `bid_blff_id_nm`
- 일정: `ibx_onbs_prnmnt_dt`, `ibx_onbs_dt`
- 문서/식별: `edoc_no`, `usr_doc_no_val`

### 연결 키
- BidNoticeDetail 및 BidOpeningResult와 동일 키(`bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`)

## 4.2 엔티티: BidOpeningResult (개찰결과, `oobsRsltList`)
### 필수 필드
- 식별자: `bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`
- 순위: `ibx_onbs_rnkg`
- 업체: `ibx_grp_nm`
- 금액/일시: `ibx_bdng_amt`, `ibx_slpr_rcptn_dt`

### 선택 필드
- 사업자/대표: `ibx_bzmn_reg_no`, `ibx_rprsv_nm`
- 입찰자: `bidr_prsn_no`, `bidr_prsn_nm`
- 사전판정: `bid_ufns_rsn_cd`, `bid_ufns_rsn_nm`, `ufns_yn`
- 평가: `ibx_evl_scr_prpl`, `ibx_evl_scr_prce`, `ibx_evl_scr_ovrl`
- 낙찰: `sfbr_slctn_ord`, `sfbr_slctn_rslt_cd`

### 연결 키
- `BidNoticeKey` + `bid_clsf_no`, `bid_prgrs_ord` 포함

## C. 정규화/중복/관계/테스트
## 5. 공통 응답(envelope)
- `result` (object|list): 실제 데이터
- `ErrorCode` (int): 0=정상, 그 외 에러
- `ErrorMsg` (str): 오류 메시지
- 처리: `ErrorCode != 0`이면 로그 기록 후 재시도/스킵 정책 적용

## 6. 정규화 규칙
- 날짜/시간: `YYYY/MM/DD HH:mm` → `datetime`
- 일시(초 포함): `YYYY/MM/DD HH:mm:ss` → `datetime`
- 금액: 콤마 제거 후 `int` 변환 (예: `1,030,000,000` → `1030000000`), 빈 값은 `null`
- 코드/코드명: 쌍으로 저장하여 조회/필터 모두 지원
- Y/N 플래그: `Y` → `True`, `N` → `False`, 그 외 `null`
- 사업자등록번호: 하이픈 제거 후 저장, 표시는 하이픈 포함 유지 (예: `120-86-77753` → `1208677753`)
- 문서번호: 공백/탭 제거 후 저장, 원본은 별도 보관 가능(표시용)

## 7. 중복 방지 키
- UNIQUE(`bid_pbanc_no`, `bid_pbanc_ord`)

## 8. 관계 정의
- BidNoticeListItem 1 ---- n BidNoticeDetail (키: `bid_pbanc_no`, `bid_pbanc_ord`)
- BidNoticeDetail 1 ---- n AttachmentItem (키: `unty_atch_file_no`)
- BidNoticeDetail 1 ---- n BidOpeningResult (키: `bid_pbanc_no`, `bid_pbanc_ord`, `bid_clsf_no`, `bid_prgrs_ord`)

## 9. 테스트 기준
- 스키마 샘플 최소 5건 확보(목록 3, 상세 2 이상)
- 필수 필드 누락/포맷 오류에 대한 validator 테스트
- 날짜/금액/플래그 정규화 케이스 테스트

## 10. 공통 키 모델 (권장)
### 엔티티: BidNoticeKey
- `bid_pbanc_no` (str)
- `bid_pbanc_ord` (str)
- `bid_clsf_no` (str|null)
- `bid_prgrs_ord` (str|null)

### 적용 범위
- 목록행, 상세(`bidPbancMap`/`pbancOrgMap`), 개찰결과 요청/응답

### 공통 필드(목록/상세 공통 분리)
- 공통(목록행 + `bidPbancMap` + `pbancOrgMap`):
  - `bid_pbanc_no`, `bid_pbanc_ord`, `bid_pbanc_num`
  - `bid_pbanc_nm`
  - `pbanc_stts_cd`, `pbanc_stts_cd_nm`
  - `prcm_bsne_se_cd`, `prcm_bsne_se_cd_nm`
  - `bid_mthd_cd`, `bid_mthd_cd_nm`
  - `std_ctrt_mthd_cd`, `std_ctrt_mthd_cd_nm`
  - `scsbd_mthd_cd`, `scsbd_mthd_cd_nm`
  - `grp_nm`
  - `pbanc_pstg_dt`, `slpr_rcpt_ddln_dt`
- 목록 전용:
  - `row_num`, `tot_cnt`, `current_page`, `record_count_per_page`, `next_row_yn`
- 상세 전용:
  - `bid_clsf_no`, `bid_prgrs_ord`, `unty_atch_file_no`

## 11. 코드/코드명 사전 (권장)
### 엔티티: CommCd
- `code_group` (str): 코드 그룹
- `code` (str): 코드
- `code_nm` (str): 코드명
- `use_yn` (str): 사용 여부

### 키 제약 (권장)
- UNIQUE(`code_group`, `code`)

## 12. 미확정 항목 트래킹 표 (권장)
### 표 필드
- `target` (str): 확인 대상 키/리스트
- `status` (str): pending/verified/removed
- `sample_id` (str): 확인한 공고번호
- `note` (str): 결론/메모

### 표 예시
| target | status | sample_id | note |
| --- | --- | --- | --- |
| `bidInfoList` 추가 필드 | pending | - | 샘플 확보 필요 |
| `pbancOrgMap` vs `bidPbancMap` 차이 | pending | - | 키 차이 비교 필요 |

## 2.1.1 요청별 추출값 요약
### 목록 조회: `selectBidPbancList.do`
- 요청 payload: `dlParamM` (기간/페이지/필터)
  - 기간/페이지: `pbancPstgStDt`, `pbancPstgEdDt`, `onbsPrnmntStDt`, `onbsPrnmntEdDt`, `currentPage`, `recordCountPerPage`
  - 필터: `bidPbancNo`, `bidPbancNm`, `prcmBsneSeCd`, `bidMthdCd`, `pbancSttsCd`, `pbancKndCd`, `stdCtrtMthdCd`, `scsbdMthdCd`
- 응답 필드(목록행):
  - 키: `bidPbancNo`, `bidPbancOrd`, `bidPbancNum`
  - 제목/상태: `bidPbancNm`, `pbancSttsCdNm`, `pbancSttsGridCdNm`, `pbancKndCdNm`
  - 분류/방식: `prcmBsneSeCdNm`, `stdCtrtMthdCdNm`, `scsbdMthdCdNm`, `bidMthdCdNm`
  - 기관/일정: `grpNm`, `pbancPstgDt`, `slprRcptDdlnDt`
  - 페이징: `totCnt`, `currentPage`, `recordCountPerPage`, `nextRowYn`

### 상세 진행정보: `selectBidPbancPrgsDetl.do`
- 요청 payload: `dlSrchCndtM`
  - 상세키: `bidPbancNo`, `bidPbancOrd`, `bidClsfNo`, `bidPrgrsOrd`, `pstNo`
- 응답에서 확인한 주요 맵/리스트
  - `pbancOrgMap`, `bidPbancMap`: 공고 상세(기간, 상태, 방식, 담당자, 기관 등) + `untyAtchFileNo`
  - `bidPbancItemlist`: 품목/서비스 항목(`ibxSrvNm`, `ibxCstrnNm`, `calFlmtTermYmd` 등)
  - 제한/조건: `bidLmtIntpList`, `bidLmtRgnList`, `dmLcnsLmtPrmsIntpList`, `dmItemMap`
  - 기타: `bdngCrstList`, `rbidList`, `bidPstmNomnEtpsList`, `bidInfoList`, `bidBsneCndtCrtrCdMap`, `bsamtMap`

### 공지/변경 공고 상세: `selectBidNoceDetl.do`
- 요청 payload: `dlSrchCndtM` + `flag: "bidDtl"`
- 응답: `result.noceList`
  - 비어있는 경우 다수
  - 채워진 샘플: `pstNo`, `bbsNo`, `pstNm`, `bulkPstCn`, `untyAtchFileNo`

### 첨부파일 목록: `selectUntyAtchFileList.do`
- 요청 payload: `dlUntyAtchFileM` (핵심 키: `untyAtchFileNo`)
- 응답: `dlUntyAtchFileL`
  - 다운로드 핵심: `atchFileNm`, `orgnlAtchFileNm`, `atchFilePathNm`, `fileExtnNm`, `fileSz`
  - 기타: `atchFileSqno`, `bsneClsfCd`, `kbrdrId`, `inptDt`, `tblNm`, `colNm`

### 파일 다운로드: `fileUpload.do` (RaonK)
- 요청 payload: `k00=...` (RaonK JS에서 생성)
- 응답: `content-disposition: attachment` + `content-type: application/zip`
- 연결 관계 요약:
  - 목록 → 상세: `bidPbancNo`, `bidPbancOrd`, `bidClsfNo`, `bidPrgrsOrd`
  - 상세 → 첨부: `untyAtchFileNo`
  - 첨부 → 다운로드: `atchFilePathNm`, `orgnlAtchFileNm`, `atchFileNm` 등이 `k00` 생성 재료로 추정

## 2.3 첨부 업로드/다운로드 관련 메모 [관찰]
### `fileUpload.do` 호출 패턴
- 동일 URL로 3회 호출됨
- Method: `POST`, `content-type: application/x-www-form-urlencoded; charset=UTF-8`
- Body 파라미터는 `k00=...` (base64 유사 문자열)
- 요청 헤더: `Origin`/`Referer` 동일, `X-CSRF-Token`은 비어있는 샘플 확인
- 응답 헤더: `x-raon-*` 헤더 포함, `content-type: text/html`
- 변형 호출: `sec-fetch-dest: iframe`, `sec-fetch-mode: navigate`, `content-type: application/x-www-form-urlencoded`

### `fileUpload.do` 응답 패턴 (예시)
- 1차: `<RAONK>[OK]...base64...</RAONK><RAONKEX>...base64...</RAONKEX>`
- 2차: `<RAONK>[OK]...토큰...</RAONK>`
- 3차: `<RAONK>[OK]</RAONK>`

### 해석 메모
- 업로드/첨부 메타 생성용으로 추정 (다운로드와는 별도)
- 다운로드는 `selectUntyAtchFileList.do`의 `atchFilePathNm` 기반 규칙 확인 필요
- `selectBidNoceDetl.do` 응답에는 `k00` 값이 포함되지 않음(샘플 기준)

### 첨부파일 다운로드 규칙 (관측)
- 다운로드 아이콘 요청은 정적 이미지(`https://nuri.g2b.go.kr/kupload/images/icon_down.gif`)로, 실제 다운로드와 무관
- 실제 다운로드는 `fileUpload.do`로 **POST** 요청되며 응답에 `content-disposition: attachment`가 포함됨
- 샘플(다운로드 클릭 시):
  - Method: `POST`
  - URL: `https://nuri.g2b.go.kr/fs/fsc/fsca/fileUpload.do`
  - Content-Type: `application/x-www-form-urlencoded`
  - Payload: `k00=...` (긴 인코딩 문자열)
  - Response:
    - `content-type: application/zip`
    - `content-disposition: attachment; filename*=utf-8''download.zip;`
    - `transfer-encoding: chunked`
  - HAR 기준 `net::ERR_ABORTED`로 보일 수 있음(브라우저 다운로드 트리거로 인한 정상 현상)
- 다운로드 클릭 시 `fileUpload.do`가 **Pre(XHR) → Document/iframe → End(XHR)** 순으로 반복 호출됨

### `k00` 생성/구성 추정 (RaonKUpload)
#### 생성 규칙(확인됨)
- `k00`는 RaonK 방식의 **문자 삽입 난독화 + base64** 결과
  - 원문(키/값)은 `VT(\\x0b)`와 `FF(\\x0c)` 구분자로 결합됨
  - base64 인코딩 후, 특정 위치에 문자 삽입
    - 삽입 순서: `r`, `a`, `o`, `n`, `w`, `i`, `z`
    - 삽입 위치(순서대로): 인덱스 `8`, `6`, `9`, `7`, `8`, `6`, `9`
  - `+`는 `%2B`로 치환됨
- 역변환(디코딩) 절차
  - URL 디코드 → 삽입 문자 제거(역순) → base64 디코드 → `VT/FF`로 split

#### `k00` 내부 파라미터 키(관찰됨)
- 공통: `kc`(요청 종류: `c10`/`c11`/`c12`), `k21`(UUID, seq)
- `c10`(pre): `k05`, `k16`, `k31`(파일명), `k30`(webPath)
- `c11`(download): `k26`(path), `k31`(파일명), `k32`(zip명)
- `c12`(end): `k26`, `k31`, `k32`

## 2.2 상세 API 스키마 [관찰]
### 엔드포인트: `selectBidNoceDetl.do`
- URL: `https://nuri.g2b.go.kr/nn/nnb/nnbb/selectBidNoceDetl.do`
- Method: `POST`

#### 요청(payload) `dlSrchCndtM`
- `pbancFlag` (str): 공고 플래그(옵션)
- `bidPbancNo` (str): 입찰공고번호
- `bidPbancOrd` (str): 차수
- `bidClsfNo` (str): 분류 번호
- `bidPrgrsOrd` (str): 진행 차수
- `bidPbancNm` (str): 공고명(옵션)
- `prcmBsneSeCd` (str): 공고분류 코드(옵션)
- `bidPbancPgstCd` (str): 공고게시 코드(옵션)
- `pbancPstgStDt` (str): 공고게시 시작일(옵션)
- `pbancPstgEdDt` (str): 공고게시 종료일(옵션)
- `recordCountPerPage` (str): 페이지 크기(옵션)
- `rowNum` (str): 행 번호(옵션)
- `kbrdrId` (str): 사용자 ID(옵션)
- `untyGrpNo` (str): 통합그룹 번호(옵션)
- `paramGbn` (str): 파라미터 구분(예: "1")
- `pstNo` (str): 게시번호(예: bidPbancNo)
- `flag` (str): 상세 유형(예: "bidDtl")
- `odn3ColCn` (str): 기타 컬럼(옵션)
- `frgnrRprsvYn` (str): 외국인대표 여부(옵션)
- `pbancInstUntyGrpNo` (str): 기관 식별자(옵션)

#### 응답(envelope)
- `result.noceList` (list[NoceItem]): 상세 공고 리스트
- `ErrorMsg` (str)
- `ErrorCode` (int)

#### 엔티티: NoceItem (샘플 기준)
- `pstNo` (str): 게시 번호
- `bbsNo` (str): 게시판/공고 번호
- `pstNm` (str): 게시 제목
- `untyAtchFileNo` (str|null): 첨부파일 그룹 키
- `useYn` (str): 사용 여부(Y/N)
- `inptDt` (datetime): 등록일시
- `odn3ColCn` (str|null): 기타 컬럼
- `bulkPstCn` (str|null): 본문/내용

### 엔드포인트: `selectUntyAtchFileList.do`
- URL: `https://nuri.g2b.go.kr/fs/fsc/fscb/UntyAtchFile/selectUntyAtchFileList.do`
- Method: `POST` (네트워크 탭 기준)

#### 요청(payload) `dlUntyAtchFileM`
- `untyAtchFileNo` (str): 첨부파일 그룹/키
- `atchFileSqnos` (str): 특정 순번 필터(옵션)
- `bsnePath` (str): 업무 경로(예: "a")
- `bsneClsfCd` (str): 업무분류 코드
- `tblNm` (str): 테이블명
- `colNm` (str): 컬럼명
- `webPathUse` (str): 웹 경로 사용 여부(Y/N)
- `isScanEnabled` (bool): 스캔 여부
- `imgUrl` (str): 이미지 URL(옵션)
- `atchFileKndCds` (str): 첨부 종류 필터(옵션)
- `ignoreAtchFileKndCds` (str): 제외 첨부 종류(옵션)
- `kbrdrIds` (str): 등록자 ID 필터(옵션)
- `kuploadId` (str): 업로드 컴포넌트 ID
- `viewMode` (str): 뷰 모드(예: "view")

#### 응답(envelope)
- `dlUntyAtchFileL` (list[AttachmentItem])
- `ErrorMsg` (str)
- `ErrorCode` (int)

#### 엔티티: AttachmentItem
- `unty_atch_file_no` (str): 첨부파일 그룹/키
- `atch_file_sqno` (int): 첨부파일 순번
- `bsne_clsf_cd` (str): 업무분류 코드
- `atch_file_knd_cd` (str): 첨부파일 종류 코드
- `atch_file_nm` (str): 저장 파일명
- `orgnl_atch_file_nm` (str): 원본 파일명
- `file_extn_nm` (str): 확장자(예: .pdf)
- `file_sz` (int): 파일 크기(bytes)
- `encr_bef_file_sz` (int|null): 암호화 전 파일 크기
- `img_url` (str|null): 이미지 URL
- `atch_file_dscr` (str|null): 첨부 설명
- `mcsc_chck_id_val` (str|null): 검사 ID
- `dwnld_prms_yn` (str|null): 다운로드 허용 여부
- `kbrdr_id` (str|null): 등록자 ID
- `kbrdr_nm` (str|null): 등록자명
- `inpt_dt` (datetime): 등록일시
- `atch_file_path_nm` (str|null): 저장 경로
- `tbl_nm` (str|null): 테이블명
- `col_nm` (str|null): 컬럼명
- `atch_file_rmrk_cn` (str|null): 비고

### 엔드포인트: `selectBidPbancPrgsDetl.do`
- URL: `https://nuri.g2b.go.kr/nn/nnb/nnbb/selectBidPbancPrgsDetl.do`
- Method: `POST`

#### 요청(payload) `dlSrchCndtM`
- `bidPbancNo` (str): 입찰공고번호
- `bidPbancOrd` (str): 차수
- `bidClsfNo` (str): 분류 번호
- `bidPrgrsOrd` (str): 진행 차수
- `paramGbn` (str): 파라미터 구분(예: "1")
- `pstNo` (str): 게시번호(예: bidPbancNo)
- `flag` (str): 상세 유형(샘플은 빈 문자열)
- 기타: `pbancFlag`, `bidPbancNm`, `prcmBsneSeCd`, `bidPbancPgstCd`,
  `pbancPstgStDt`, `pbancPstgEdDt`, `recordCountPerPage`, `rowNum`,
  `kbrdrId`, `untyGrpNo`, `odn3ColCn`, `frgnrRprsvYn`, `pbancInstUntyGrpNo`

#### 응답(envelope)
- `result.bidPbancMap` (dict): 상세 공고 핵심(공고/일정/기관/연락처 등)
- `result.pbancOrgMap` (dict): 원본/기관 관련 맵(필드 유사)
- `result.bidPbancItemlist` (list): 품목/사업 항목 리스트
- `result.bidInfoList` (list)
- `result.bidLmtRgnList` (list)
- `result.bidLmtIntpList` (list)
- `result.dmLcnsLmtPrmsIntpList` (list)
- `result.bdngCrstList` (list)
- `result.rbidList` (list)
- `result.bidPstmNomnEtpsList` (list)
- `result.ryrcnCnt` (int): 재입찰 횟수
- `result.dmItemMap` (dict): 제한 조건 요약
- `result.bidBsneCndtCrtrCdMap` (dict): 조건/서식 메타
- `result.bsamtMap` (dict|null): 금액 관련 맵
- `ErrorMsg` (str)
- `ErrorCode` (int)

#### `bidPbancMap` / `pbancOrgMap` 주요 필드(발췌)
- 공고 식별: `bidPbancNo`, `bidPbancOrd`, `bidPbancNum`, `bidPbancFullNo`
- 분류/방식: `prcmBsneSeCd`, `prcmBsneSeCdNm`, `bidPbancPgstCd`,
  `bidMthdCd`, `bidMthdCdNm`, `scsbdMthdCd`, `scsbdMthdCdNm`,
  `stdCtrtMthdCd`, `stdCtrtMthdCdNm`
- 기관/담당: `pbancInstUntyGrpNo`, `pbancInstUntyGrpNoNm`, `grpNm`,
  `picId`, `picIdNm`, `bidBlffId`, `bidBlffIdNm`, `bsneEml`, `bsneTlphNo`, `bsneFaxNo`
- 일정: `slprRcptBgngDt`, `slprRcptDdlnDt`, `onbsPrnmntDt`, `bidQlfcRegDt`,
  `pbancPstgDt`
- 장소/주소: `onbsPlacNm`, `zip`, `baseAddr`, `dtlAddr`, `untyAddr`
- 부가 플래그: `rbidPrmsYn`, `pbancPstgYn`, `bofcBdngPrmsYn`, `rgnLmtYn`,
  `lcnsLmtYn`, `qlemTrgtYn`, `vatAplcnYn`, `pbancDscrTrgtYn`, `pnprUseYn`
- 첨부 연계: `untyAtchFileNo`

#### `bidPbancItemlist` 필드(발췌)
- `bidPbancNo`, `bidPbancOrd`, `bidClsfNo`
- `bidPbancItemSqno` (int): 항목 순번
- `ibxSrvNm` (str): 용역/사업명
- `ibxSrstNm` (str): 사업/위치 요약
- `calFlmtTermYmd` (str): 완료 기한(YYYYMMDD)

#### 샘플 기반 전체 키 목록 (현재 샘플 1건 기준)
- `pbancOrgMap` / `bidPbancMap` 공통 키:
  `bidPbancNo`, `bidPbancOrd`, `bidPbancNum`, `bidPbancFullNo`, `prcmBsneSeCdOn`,
  `prcmBsneSeCd`, `prcmBsneSeCdNm`, `bidPbancPgstCd`, `ctrtTyCd`, `bidPbancNm`,
  `pbancInstUntyGrpNo`, `pbancInstUntyGrpNoNm`, `bzmnRegNo`, `dmstUntyGrpNo`,
  `picId`, `picIdNm`, `picIdBaseTlphNo`, `bidBlffId`, `bidBlffIdNm`, `bidMthdCd`,
  `bidMthdCdNm`, `scsbdMthdCd`, `scsbdMthdCdNm`, `pbancSttsCd`, `pbancSttsCdNm`,
  `stdCtrtMthdCd`, `stdCtrtMthdCdNm`, `slprRcptBgngDt`, `slprRcptBgngDtYmd`,
  `slprRcptBgngDtHr`, `slprRcptDdlnDt`, `slprRcptDdlnDtYmd`, `slprRcptDdlnDtHr`,
  `slprRcptDdlnDtIndt`, `onbsPrnmntDt`, `onbsPrnmntDtYmd`, `onbsPrnmntDtHr`,
  `onbsPrnmntDtIndt`, `ibxOnbsPrnmntDt`, `ibxOnbsDt`, `onbsPlacCd`, `onbsPlacNm`,
  `bidQlfcRegDt`, `bidQlfcRegDtYmd`, `bidQlfcRegDtHr`, `pnprDcsnMthoCd`,
  `rbidPrmsYn`, `rbidPrmsYnLtrs`, `pbancKndCd`, `pbancKndCdNm`, `emrgPbancYn`,
  `emrgPbancYnLtrs`, `prspPrce`, `pbancPstgDt`, `pbancPstgDtYmd`, `pbancPstgDtHr`,
  `pbancPstgYn`, `pbancPstgYnLtrs`, `bofcBdngPrmsYn`, `bofcBdngPrmsYnLtrs`,
  `bidPrcpLmtYn`, `bidPrcpLmtYnLtrs`, `rgnLmtYn`, `rgnLmtYnLtrs`, `lcnsLmtYn`,
  `lcnsLmtYnLtrs`, `evlScrRlsYn`, `evlScrRlsYnLtrs`, `fbidRsnCd`, `qlemTrgtYn`,
  `qlemTrgtYnLtrs`, `emrgOderBizSeCd`, `emrgOderRsnCd`, `evlcrtAmt`, `totlEvlcrtAmt`,
  `vatAmt`, `vatAplcnYn`, `vatAplcnYnLtrs`, `hsmpMngOfceTlphNo`, `pbancDscrTrgtYn`,
  `pbancDscrTrgtYnLtrs`, `pnprUseYn`, `pnprUseYnLtrs`, `pnprRlsYn`, `pnprRlsYnLtrs`,
  `prspAmt`, `pbancBfssRcptDt`, `pbancBfssDt`, `pbancBfssDtYmd`, `pbancBfssDtHr`,
  `pbancBfssPlacNm`, `bfssPicId`, `pbancBfssDocPcstCd`, `minReduRt`,
  `etpsMaxBdngNotm`, `atmtExtsTmmn`, `kbrdrId`, `inptDt`, `edocNo`, `usrDocNoVal`,
  `bidDepoPayTermDt`, `bidDepoPayTermDtYmd`, `bidDepoPayTermDtHr`, `alotBgtAmt`,
  `cvlnPbancNmcptEtpsRlsYn`, `cvlnPbancNmcptEtpsRlsYnLtrs`, `bidPrceAlpt`,
  `bidPrplAlpt`, `untyAtchFileNo`, `impvBizYn`, `lcrtTyCd`, `cvlnQlemCrtrNm`,
  `cvlnQlemCrtrNo`, `slprRcptBgngYn`, `slprRcptDdlnYn`, `onbsPrnmntYn`, `pbancBfssYn`,
  `pbancChgRsn`, `pvctRsn`, `rtrcnRsn`, `cornPbancRsn`, `emrgPbancRsn`,
  `hsmpWefrFcltDtlCn`, `hsmpHmpgUrl`, `fcrgPbancCratCn`, `bidClsfNo`, `bidPrgrsOrd`,
  `prcsRsn`, `untyGrpNo`, `grpNm`, `grpSeCd`, `hsmpSqms`, `hsmpMgcsLevySqms`,
  `hsmpHshdCnt`, `hsmpBldgCnt`, `hsmpHeatMthoCd`, `hsmpHeatMthoCdNm`, `mngOfceTlphNo`,
  `zip`, `baseAddr`, `dtlAddr`, `hmpgUrl`, `untyAddr`, `cvlnOrbySeCd`, `bsneTlphNo`,
  `bsneFaxNo`, `ogdpDeptNm`, `ogdpJbttlNm`, `sfbrSlctnRsltCd`, `bdwetpsUntyGrpNo`,
  `bdwetpsUntyGrpNm`, `bsneEml`, `usrNm`, `rlsYn`, `pstmEtpsYn`, `chgDataYn`,
  `pbancPicId`, `pbancPicNm`
- `bidPbancItemlist` 전체 키:
  `bidPbancNo`, `bidPbancOrd`, `bidClsfNo`, `bidPbancItemSqno`, `sbxDevyCndtCd`,
  `ibxItemCfnm`, `calDlvgdsTermYmd`, `calDlvgdsTermYmdLtrs`, `ibxDlvgdsPlacNm`,
  `ibxCvlnPbancQty`, `ibxCstrnNm`, `calCmcnTermYmd`, `calCmcnTermYmdLtrs`,
  `ibxCntstNm`, `ibxSrvNm`, `calFlmtTermYmd`, `calFlmtTermYmdLtrs`,
  `ibxSrstNm`, `sbxPrchsDtlItemUntVal`

#### `bdngCrstList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)
- `bidClsfNo` (str)
- `bidPrgrsOrd` (str)
- `bdngAmt` (int): 투찰 금액
- `plrlCnt` (int): 복수 카운트
- `etpsCnt` (int): 업체 수

#### `bidInfoList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)

#### `bidPstmNomnEtpsList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)
- `ibxEtpsUntyGrpNo` (str): 입력된 사업자/단체번호
- `etpsUntyGrpNo` (str): 업체 통합그룹 번호
- `kbrdrId` (str): 등록자 ID
- `inptDt` (datetime): 등록일시
- `ibxBzmnRegNo` (str): 입력된 사업자등록번호
- `ibxGrpNm` (str): 입력된 업체명
- `ibxRprsvNm` (str): 입력된 대표자명

#### `bidLmtIntpList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)
- `bidLmtKndCd` (str): 입찰제한 종류 코드
- `bidLmtGupSqno` (int): 제한 그룹 순번
- `sbxBidLmtGupSqno` (int): 화면 표시용 그룹 순번
- `bidLmtSqno` (int): 제한 항목 순번
- `intpRgnSeCd` (str): 제한 구분 코드
- `sbxIntpRgnUntyCd` (str): 제한 코드
- `sbxBidLmtUntyCd` (str): 제한 코드(중복)
- `sbxIntpRgnUntyCdNm` (str): 제한명
- `sbxBidLmtUntyCdNm` (str): 제한명(중복)
- `cnscAbltEvlAmt` (str|null): 능력평가 금액
- `lgdngNm` (str|null): 법정동명
- `ctpvCd` (str|null): 시도 코드
- `sgnguCd` (str|null): 시군구 코드
- `sgnguNm` (str|null): 시군구명
- `wdarSfgvYn` (str|null): 우대 여부

#### `bidLmtRgnList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)
- `bidLmtKndCd` (str): 입찰제한 종류 코드
- `bidLmtGupSqno` (int): 제한 그룹 순번
- `sbxBidLmtGupSqno` (int): 화면 표시용 그룹 순번
- `bidLmtSqno` (int): 제한 항목 순번
- `intpRgnSeCd` (str): 제한 구분 코드
- `sbxIntpRgnUntyCd` (str): 제한 코드
- `sbxBidLmtUntyCd` (str): 제한 코드(중복)
- `sbxIntpRgnUntyCdNm` (str|null): 제한명
- `sbxBidLmtUntyCdNm` (str|null): 제한명(중복)
- `cnscAbltEvlAmt` (str|null): 능력평가 금액
- `lgdngNm` (str|null): 법정동명
- `ctpvCd` (str|null): 시도 코드
- `sgnguCd` (str|null): 시군구 코드
- `sgnguNm` (str|null): 시군구명
- `wdarSfgvYn` (str|null): 우대 여부

#### `rbidList` 필드(샘플 확인됨)
- `bidPbancNo` (str)
- `bidPbancOrd` (str)
- `bidClsfNo` (str)
- `bidPrgrsOrd` (str)
- `slprRcptDdlnDt` (datetime): 재입찰 마감일시
- `onbsPrnmntDt` (datetime): 재입찰 개찰일시
- `bidPgstCd` (str): 공고게시 코드
- `bidPgstCdNm` (str): 공고게시 코드명
- `bidPbancNm` (str): 공고명

#### `dmLcnsLmtPrmsIntpList` 필드(샘플 확인됨)
- `bidLmtUntyCd` (str): 제한 업종 코드
- `lmtIntpNm` (str): 제한 업종명(코드 포함)
- `bidPrmsIntpCd` (str): 허용 업종 코드
- `bidPrmsIntpNm` (str): 허용 업종명(코드 포함)

#### `bsamtMap` 필드(샘플 확인됨)
- `bsamtCmpuOrd` (str): 기초금액 산정 순번
- `bsamt` (int): 기초금액
- `bsamtEncrVal` (str): 기초금액 암호값
- `inptDt` (datetime): 등록일시

#### 샘플 상태 메모
- 현재 샘플에서는 `bidInfoList` 등 다수 리스트가 빈 배열
- `bsamtMap`도 null → 금액 관련 맵은 다른 샘플 필요
- `bdngCrstList`는 비어있지 않은 샘플 확인됨
- `bidInfoList`는 최소 키(`bidPbancNo`, `bidPbancOrd`) 확인됨
- `bidPstmNomnEtpsList`는 비어있지 않은 샘플 확인됨
- `bidLmtIntpList`는 비어있지 않은 샘플 확인됨
- `dmItemMap.intpLmtCn`(HTML 문자열) 확인됨
- `bidLmtRgnList`는 비어있지 않은 샘플 확인됨
- `dmItemMap.rgnLmtGuidCn`, `dmItemMap.rgnLmtCn` 확인됨
- `rbidList`는 비어있지 않은 샘플 확인됨
- `dmLcnsLmtPrmsIntpList`는 비어있지 않은 샘플 확인됨
- `bsamtMap`는 비어있지 않은 샘플 확인됨

### 응답(envelope)
- `result` (list[BidNoticeListItem]): 목록 결과
- `ErrorMsg` (str): 처리 메시지
- `ErrorCode` (int): 처리 코드(0=정상)

## D. 보완 항목/트래킹
## 2.1.2 추가 수집 필요 항목 [미확정]
- `bidInfoList`에 `bidPbancNo/bidPbancOrd` 외 필드 존재 여부
- `bidLmtRgnList.sbxIntpRgnUntyCdNm` 값이 채워지는 샘플
- `dmLcnsLmtPrmsIntpList` 추가 키 존재 여부
- `rbidList`에 결과/사유 등 추가 메타 존재 여부
- `pbancOrgMap` vs `bidPbancMap` 키 차이 여부

## 2.1.3 샘플 확보 현황
- `bidLmtIntpList.sbxIntpRgnUntyCdNm` 채워진 샘플 확보
  - 예: `R26BK01320434`에서 값 `"도시 및 주거환경 정비사업전문관리업"`
  - 추가 예: `R26BK01296848` (입찰 제한/지역/업종 리스트는 비어있음)
- 추가 예: `R26BK01294070` (입찰 제한/지역/업종 리스트는 비어있음)
- 추가 예: `R25BK00821183` (재공고/물품, `bidPbancItemlist`에 `ibxItemCfnm`/`calDlvgdsTermYmd`/`ibxCvlnPbancQty` 등 확인)
- 추가 예: `20241142507` (재공고/용역, `bsamtMap.bsamtCmpuOrd`=`000`, `bsamt`/`bsamtEncrVal` null)
- 추가 예: `20241205759` (재공고/용역, `pnprDcsnMthoCd` 값 존재, `pnprRlsYn` null)
- 추가 예: `20241137429` (재공고/용역, `bidLmtIntpList`에 업종명 `"여객자동차운송사업(구역여객자동차운송사업-전세버스)"`)
- 추가 예: `20241137420` (재공고/용역, `bidLmtIntpList`에 동일 업종명 확인)
- 추가 예: `20240920435` (재공고/공사, `bidLmtRgnList`에 `lgdngNm`/`ctpvCd`/`sgnguCd`/`sgnguNm` 존재하지만 `sbxIntpRgnUntyCdNm`은 null, `dmLcnsLmtPrmsIntpList` 4키 확인)
- 추가 예: `R25BK00565062` (재공고/공사, `bidPstmNomnEtpsList` 채워짐, `bidInfoList`는 `bidPbancNo`/`bidPbancOrd`만 확인)
- 추가 예: `R25BK00782209` (재공고/공사, `bidPstmNomnEtpsList` 채워짐, `bidInfoList`는 비어있음)
- 추가 예: `R25BK00750015` (재공고/용역, `bidPstmNomnEtpsList` 채워짐, `bidLmtIntpList` 비어있음)
- 추가 예: `R25BK00606851` (변경공고/용역, `bidInfoList`는 `bidPbancNo`/`bidPbancOrd`만 확인, `bidPrceAlpt`/`bidPrplAlpt` 값 존재)
- 추가 예: `R26BK01299166` (`rbidList` 채워짐: `bidClsfNo`, `bidPrgrsOrd`, `slprRcptDdlnDt`, `onbsPrnmntDt`, `bidPgstCd`, `bidPgstCdNm`, `bidPbancNm`)
- 추가 예: `R25BK00887892` (`rbidList` 채워짐: 동일 필드, 공고 진행 차수 0/1 확인)
- 추가 예: `T25BK00567855` (`bidLmtRgnList` 복수 행, `lgdngNm`/`ctpvCd`/`sgnguCd` 값 확인. `sbxIntpRgnUntyCdNm`은 여전히 null)
- 추가 예: `T25BK01161170` (`bidLmtRgnList` 복수 행, `bidInfoList`는 `bidPbancNo`/`bidPbancOrd`만 확인, `sbxIntpRgnUntyCdNm`은 null)
- 추가 예: `20150911689` (`bidLmtIntpList` 다중 업종명 확인, `bidInfoList`는 기본 필드만 확인)
- 추가 예: `20150100563` (`bidPbancItemlist`에 `sbxDevyCndtCd`/`ibxItemCfnm`/`calDlvgdsTermYmd`/`ibxDlvgdsPlacNm`/`ibxCvlnPbancQty` 값 확인)
