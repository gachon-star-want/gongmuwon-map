# P2-P4 Public-Sector Expansion Status

작성일: 2026-06-02

## 범위

- P2 중앙행정기관·헌법기관·독립기관: 60개
- P3 지정 공공기관: 342개
- P4 지방공공기관: 1,312개
- 총계: 1,714개

P1 지방자치단체·의회 486개는 이번 확장 권역과 분리한다.

## Source Registry 분류

`public-officer-pipeline source-registry --scope nationwide --summary-only` 기준 P2-P4는 pending 0개다.

| 구분 | total | verified_in_code | source_not_found | no_recent_data | pdf_vision_hold | adapter_hold | pending |
|---|---:|---:|---:|---:|---:|---:|---:|
| P2 | 60 | 0 | 60 | 0 | 0 | 0 | 0 |
| P3 | 342 | 1 | 0 | 277 | 8 | 56 | 0 |
| P4 | 1,312 | 0 | 0 | 0 | 0 | 1,312 | 0 |
| 합계 | 1,714 | 1 | 60 | 277 | 8 | 1,368 | 0 |

## 공식 출처와 보류 기준

### P2

- 기준 출처: 정부조직관리정보시스템 2026 정부기구도
- 상태: source_not_found 60개
- 검색 경로: 기관 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴, 기관장/장차관 업무추진비 키워드, 정보공개포털(open.go.kr)
- 보류 이유: place-level 적재에 필요한 기관별 공식 원문 URL, 공공누리 제1유형 또는 동등한 자유이용 근거, 첨부 접근성을 확정하지 못함

### P3

- 기준 출처: 잡알리오 2026 공공기관 지정현황, ALIO 경영공시 항목 20701(기관장 업무추진비)
- 라이선스 근거: https://www.alio.go.kr/notice/copyright.do
- production 적재 완료: 게임물관리위원회
- 최근 12개월 place-level 0건: 277개
- PDF vision 보류: 8개
- adapter/parser 보류: 56개
  - 금액 천원 단위 보정 필요: 6개
  - HWP parser 필요: 2개
  - ALIO 다운로드/fileNo 보강 필요: 14개
  - XLS 구조 보강 필요: 34개

### P4

- 기준 출처: 클린아이 정책자료 2026.3.31 기준 지방공공기관 현황
- 후보 출처:
  - 지방공기업 기관장 업무추진비 통계: https://www.cleaneye.go.kr/user/headOrgWorkCostStat.do
  - 지방공기업 기관별공시: https://www.cleaneye.go.kr/user/itemGongsi.do
  - 지방출자출연 기관별공시: https://www.cleaneye.go.kr/user/iptItemGongsi.do
- 라이선스 근거: https://www.cleaneye.go.kr/user/copyrightPolicy.do
- 상태: adapter_hold 1,312개
- 보류 이유: CleanEye entId/itemId/itemNo 연계, `fn_FileDown`/`/file/FileDownload.do`, 기관명 정규화 매핑, aggregate 통계와 place-level 세부내역 분리 adapter가 아직 없음

## Production 적재

게임물관리위원회만 dry-run 통과 후 production write를 수행했다.

| 기관 | source | places | visits | raw rows | normalized visits | Kakao matched places |
|---|---:|---:|---:|---:|---:|---:|
| 게임물관리위원회 | 1 | 51 | 109 | 157 | 109 | 40/51 |

검증:

- dry-run: success, raw_parsed_rows 157, parsed_rows 109, normalized_visits 109
- production write: loaded_sources 1, loaded_places 51, loaded_visits 109
- refresh-views: `place_grade_v1`, `agency_stats_v1` refreshed
- API after: agency_count 487, place_count 12169, visit_count 24554

P2-P4 production DB seed 상태:

- bulk seed는 수행하지 않았다.
- loader가 production write 배치에서 필요한 agency row만 upsert한다.
- 현재 P2-P4 agency row는 P3 게임물관리위원회 1개다.
