# 전국 수집 검증 리포트

주의: 이 리포트는 입력 JSON의 집계값만 사용하며 원문 행, 개인정보, 연결 문자열을 포함하지 않는다.

## 실행 메타데이터

| 항목 | 값 |
|---|---|
| generated_at | 2026-06-01T06:07:49.131Z |
| workflow | - |
| event | - |
| run_id | local-dryrun-timeboxed |
| run_attempt | - |
| actor | - |
| commit_sha | local |
| artifact | local-artifacts |
| staging_branch | nationwide-staging-20260601 |

## 실행 게이트

| 게이트 | 상태 | 판정 |
|---|---|---|
| production 기준선 read-only 리포트 | 완료 | 통과 |
| production 기준선 SQL 성공 | 완료 | 통과 |
| source registry 전국 카운트 | 완료 | 통과 |
| source registry total/count validity | 완료 | 통과 |
| staging before baseline | 완료 | 통과 |
| staging before baseline SQL 성공 | 완료 | 통과 |
| staging after baseline | 완료 | 통과 |
| staging after baseline SQL 성공 | 완료 | 통과 |
| nationwide dry-run | 미완료 | 차단 |
| dry-run collection activity | 완료 | 통과 |
| dry-run retry policy | 완료 | 통과 |
| staging load | 미완료 | 차단 |
| staging load row activity | 미완료 | 차단 |
| staging load retry policy | 미완료 | 차단 |
| public route contract | 완료 | 통과 |
| production write approval | 미완료 | 차단 |

서비스 주입 판정: production 주입 불가

## Production 기준선

| 항목 | 값 |
|---|---:|
| target | readonly |
| agencies | 52 |
| sources | 227 |
| places | 5,018 |
| place_visits | 11,327 |
| agencies_public | 52 |
| places_public | 5,018 |
| place_visits_public | 11,327 |
| visit date range | 2024-01-02 ~ 2026-05-22 |
| distinct visit dates | 606 |
| agencies with visits | 51 |
| agencies without visits | 1 |
| Kakao matched places | 3,555 / 5,018 (70.8%) |
| coordinate places | 3,780 / 5,018 (75.3%) |
| representative stored visits | 0 / 11,327 |
| avg extractor confidence | 0.82 |

## Production 기준선 Source Files

| file_kind | count | missing_storage_path | min_published | max_published |
|---|---:|---:|---|---|
| pdf | 126 | 126 | 2026-02-03 | 2026-05-26 |
| html | 69 | 69 | - | - |
| xlsx | 20 | 20 | 2026-02-09 | 2026-05-22 |
| xls | 12 | 12 | 2024-04-18 | 2026-04-18 |


## Staging 기준선 Before

| 항목 | 값 |
|---|---:|
| target | staging |
| agencies | 52 |
| sources | 227 |
| places | 5,018 |
| place_visits | 11,327 |
| agencies_public | 52 |
| places_public | 5,018 |
| place_visits_public | 11,327 |
| visit date range | 2024-01-02 ~ 2026-05-22 |
| distinct visit dates | 606 |
| agencies with visits | 51 |
| agencies without visits | 1 |
| Kakao matched places | 3,555 / 5,018 (70.8%) |
| coordinate places | 3,780 / 5,018 (75.3%) |
| representative stored visits | 0 / 11,327 |
| avg extractor confidence | 0.82 |

## Staging 기준선 Before Source Files

| file_kind | count | missing_storage_path | min_published | max_published |
|---|---:|---:|---|---|
| pdf | 126 | 126 | 2026-02-03 | 2026-05-26 |
| html | 69 | 69 | - | - |
| xlsx | 20 | 20 | 2026-02-09 | 2026-05-22 |
| xls | 12 | 12 | 2024-04-18 | 2026-04-18 |


## Staging 기준선 After

| 항목 | 값 |
|---|---:|
| target | staging |
| agencies | 2,200 |
| sources | 227 |
| places | 5,018 |
| place_visits | 11,327 |
| agencies_public | 2,200 |
| places_public | 4,785 |
| place_visits_public | 10,842 |
| visit date range | 2024-01-02 ~ 2026-05-22 |
| distinct visit dates | 606 |
| agencies with visits | 51 |
| agencies without visits | 2,149 |
| Kakao matched places | 3,555 / 5,018 (70.8%) |
| coordinate places | 3,780 / 5,018 (75.3%) |
| representative stored visits | 0 / 11,327 |
| avg extractor confidence | 0.82 |

## Staging 기준선 After Source Files

| file_kind | count | missing_storage_path | min_published | max_published |
|---|---:|---:|---|---|
| pdf | 126 | 126 | 2026-02-03 | 2026-05-26 |
| html | 69 | 69 | - | - |
| xlsx | 20 | 20 | 2026-02-09 | 2026-05-22 |
| xls | 12 | 12 | 2024-04-18 | 2026-04-18 |


## Source Registry

| 그룹 | total | verified | pending | legal_hold | invalid |
|---|---:|---:|---:|---:|---:|
| p1 | 486 | 139 | 280 | 67 | 0 |
| p2 | 60 | 0 | 60 | 0 | 0 |
| p3 | 342 | 0 | 342 | 0 | 0 |
| p4 | 1,312 | 0 | 1,312 | 0 | 0 |
| 합계 | 2,200 | 139 | 1,994 | 67 | 0 |


## 전국 Dry Run

| 항목 | 값 |
|---|---:|
| ok | false |
| scope | nationwide |
| dry_run | true |
| write_target | staging |
| concurrency | 12 |
| max_attempts | 5 |
| agency_timeout_seconds | 60 |
| total | 2,200 |
| success | 47 |
| adapter_required | 2,061 |
| unsupported | 0 |
| config_error | 2 |
| failed | 90 |
| posts_seen | 142 |
| posts_fetched | 16 |
| raw_parsed_rows | 170 |
| parsed_rows | 52 |
| normalized_visits | 52 |
| places_seen | 49 |
| kakao_matched_places | 47 |
| loaded_sources | 0 |
| loaded_places | 0 |
| loaded_visits | 0 |
| skipped_invalid_places | 0 |


| failure_reason | agencies |
|---|---:|
| timeout | 90 |
| legal_hold | 67 |
| source_not_found | 1,994 |
| kakao_resolution | 1 |
| llm_extraction_failure | 1 |

## 전국 Dry Run Agency Retry Evidence

| agency | region | adapter | result | failure_reason | attempts | timeout_stage | last_error |
|---|---|---|---|---|---:|---|---|
| 강북구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 강동구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 강서구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 관악구청 | 서울특별시 | estimate_list_html | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 광진구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 서울시청 | 서울특별시 | seoul_opengov | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 강북구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 강서구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 관악구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 구로구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 광진구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 마포구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 동작구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 서대문구청 | 서울특별시 | inline_expense_table | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 금천구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 마포구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 동대문구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 동작구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 도봉구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 서대문구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 도봉구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 노원구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 구로구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 영등포구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 서초구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 성북구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 양천구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 양천구의회 | 서울특별시 | council_attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 성동구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |
| 서초구청 | 서울특별시 | attachment_board | failed | timeout | 5 | - | agency timed out after 60 seconds |


## 표적 Dry Run 진단

전국 dry-run이 차단된 상태에서 개별 수정 경로를 검증한 보조 증거다. production 주입 판정에는 전국/staging 게이트만 사용한다.

| label | ok | result | failure_reason | timeout_stage | posts_fetched | raw_parsed_rows | parsed_rows | normalized_visits | places_seen | kakao_matched_places | note |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 강북_5초_진단 | false | failed | timeout | extract_rows | 0 | 0 | 0 | 0 | 0 | 0 | agency timed out after 5 seconds |
| 강북_180초_진단 | true | success | - | - | 1 | 10 | 10 | 10 | 7 | 7 | - |
| 성남_warn | true | success | - | - | 2 | 21 | 21 | 21 | 20 | 18 | - |
| 성남_strict | false | config_error | kakao_resolution | - | 1 | 18 | 18 | 18 | 17 | 15 | quality gate failed: missing_coordinates: missing coordinate ratio exceeds threshold: 2/17 > 0.05 |
| 대전_strict | true | success | - | - | 1 | 10 | 10 | 10 | 10 | 10 | - |
| 구로_strict | false | config_error | kakao_resolution | - | 1 | 13 | 13 | 13 | 12 | 11 | quality gate failed: missing_coordinates: missing coordinate ratio exceeds threshold: 1/12 > 0.05 |
| 보령진도_current_window | true | success | - | - | 2 | 26 | 0 | 0 | 0 | 0 | - |
| 보령진도_row_window | true | success | - | - | 2 | 26 | 22 | 22 | 19 | 0 | - |


## Staging Load

입력 JSON 없음.

## Staging Load Agency Retry Evidence

results[] 입력 없음.

## 다음 액션

- 차단 게이트가 남아 있으면 production write를 실행하지 않는다.
- staging load가 끝난 뒤 npm run check:public-contracts를 실행하고 --public-contract=pass로 리포트를 재생성한다.
- production write는 별도 승인 후 --write-target production --confirm-production-write --allow-production-write --production-gate-report <검증리포트>로만 실행한다.
