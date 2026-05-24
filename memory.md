# 작업 메모리

## 2026-05-24 재개 체크포인트

- Phase 1 완료 증거:
  - Neon project: `round-wind-92313772` (`gongmuwon-map`)
  - R2 bucket: `officer-map-raw`
  - Seoul City Hall 적재: `place_visits=175`, `places=148`
  - `places_public` readonly role 조회 성공: `148`
  - `place_grade_v1` graded rows: `148`
  - representative 정책 위반: `0`
  - Kakao match rate: `89.19%`
- 검증 완료:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 7 passed
  - `npm run build` → passed
  - API TypeScript compile → passed
  - MD 운영자 미확정 토큰 grep → 0건
- GitHub 백업:
  - `4ef4fc2` — Neon/Vercel API Routes 전환
  - `a08a97f` — Kakao placeId 중복 upsert 수정
- 현재 진행:
  - Phase 2 프론트 MVP 작업 중
  - 로컬 미커밋 변경: `apps/web/src/App.tsx`, `apps/web/src/styles.css`
- 주의:
  - 실제 Phase 1 적재는 deterministic normalizer로 수행. Anthropic 응답 비JSON 케이스는 parser 보강 완료.
  - Phase 2의 51개 기관 백필은 아직 구현/검증 전. 먼저 52기관 마스터/백필 실행 구조와 프론트 MVP 검증이 필요.

## 2026-05-24 Phase 2 프론트 중간 체크포인트

- 구현 완료:
  - React/Mantine 기반 지도형 MVP로 교체
  - `/api/v1/places`, `/api/v1/places/{id}/visits` fetch 연결
  - 자치구, 등급, 폐업 포함, 검색, 상세/목록 패널 필터 동작 구현
  - Kakao JS 키가 있으면 카카오맵, 없으면 좌표 기반 fallback map 사용
  - 폐업 신고 모달 → `POST /api/closure-report` 연결
  - `/api/v1/stats/summary`, `/api/sitemap`, 정적 `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/openapi.json` 추가
- 검증 완료:
  - `npm run build` → passed
  - API TypeScript compile → passed
- 다음 작업:
  - Vercel env에 Neon/R2/Kakao/cron 값 주입
  - production deploy 후 API/프론트 렌더링 QA
  - 52기관 백필은 현재 서울 정보소통광장 단일 크롤러만 있어, 기관 마스터 생성 + 백필 구조 또는 제한적 대체 검증 필요

## 2026-05-24 배포 환경 체크포인트

- Vercel Production env 주입 완료:
  - `DATABASE_URL`, `DATABASE_URL_READONLY`, `VITE_KAKAO_JS_KEY`, `KAKAO_REST_KEY`, `CRON_SECRET`
- Vercel Development env 주입 완료.
- Vercel Preview env:
  - 전체 preview는 CLI가 `git_branch_required`를 반환.
  - `main`은 production branch라 preview env 대상으로 지정 불가.
  - production 배포에는 영향 없음.
- GitHub Actions secrets 주입 완료:
  - `DATABASE_URL`, `DATABASE_URL_READONLY`, `KAKAO_REST_KEY`, `KAKAO_JS_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`
- Production deploy:
  - deployment id: `dpl_HENmaZfkVaD1ndVurni8obEvfm26`
  - canonical alias: `https://xn--ob0bo0wl1ax52a.com`
- Production API smoke:
  - `/api/v1/stats/summary` → `place_count=148`, `visit_count=175`, `agency_count=1`
  - `/api/v1/places?...limit=3` → data returned
- 발견/수정:
  - `/sitemap.xml` HEAD가 405였음. `methodGuard`에서 `HEAD`를 GET 허용 핸들러로 통과시키도록 수정.

## 2026-05-24 Phase 2 렌더링 QA 체크포인트

- Production 렌더링 QA:
  - `https://xn--ob0bo0wl1ax52a.com` 데이터 fetch 정상.
  - `/api/v1/places?bbox=...&limit=500` → 200.
  - `/api/v1/places/{id}/visits?limit=50` → 200.
  - 콘솔 에러 없음.
- 발견/수정:
  - Kakao JS SDK 요청이 headless QA에서 pending 상태로 남으면 중앙 지도 영역이 빈 화면으로 보였음.
  - SDK 준비 전 또는 실패/타임아웃 시 좌표 기반 fallback map을 렌더하도록 `MapCanvas`와 `loadKakao`를 수정.
- 재검증:
  - `npm run build` → passed
  - API TypeScript compile → passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 7 passed

## 2026-05-24 Phase 2 셀프 체크 결과

- 통과:
  - Production 지도 + 마커 + 상세 패널 렌더링 정상.
  - 검색 필터 동작 확인 (`삼우정` 검색 시 1건으로 축소).
  - 등급 필터와 목록 전환 UI 동작 확인.
  - 모바일 375x812 뷰포트에서 주요 UI 겹침 없음.
  - `/llms.txt` HEAD → 200.
- 실패:
  - `place_visits` row: `175` (`> 10,000` 기준 미달).
  - 적재 기관: `1/52` (`>=45/52` 기준 미달).
  - sitemap URL: `155` 추정 (`7` static + `148` places, `1,000+` 기준 미달).
  - 51개 기관 백필은 아직 실제 어댑터/수집 성공 증거 없음.
- Runbook 결정:
  - Phase 2 체크 실패이므로 Phase 3 진입 금지.
  - 사용자 확인 필요: 서울시청 단일 소스 MVP로 배포 완료 처리할지, 51개 기관 어댑터/백필을 계속 구현할지 결정해야 함.

## 2026-05-24 Phase 2 백필 재개 체크포인트

- 구현:
  - `public_officer_pipeline.agencies`에 v1 서울 52기관 마스터 추가.
  - `public-officer-pipeline seed-agencies` CLI 추가.
  - `run-opengov-agency <agency>` CLI 추가: `source_pattern.adapter == seoul_opengov` 기관을 동일 파이프라인으로 실행.
  - `refresh-views` CLI 추가: `place_grade_v1`, `agency_stats_v1` 갱신.
- 실제 적용:
  - Neon에 기관 52개 seed 완료.
  - Production stats API에서 `agency_count=52` 확인.
  - 서울시의회(`의회사무처`) 5개 게시글 실제 적재:
    - `posts_seen=50`
    - `posts_fetched=5`
    - `parsed_rows=14`
    - `normalized_visits=14`
    - `loaded_sources=4`
    - `loaded_places=14`
    - `loaded_visits=14`
    - Kakao match rate `85.71%`
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, `agencies_with_visits=2`, `agency_stats_visit_sum=189`.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 11 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - `npm run build` → passed
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`189`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`2/52`).
  - 구청/구의회 50개 기관은 정보소통광장 단일 패턴이 아니라 개별 게시판/PDF/HWP/XLSX 어댑터가 필요.

## 2026-05-24 강남구청 XLSX 어댑터 체크포인트

- 구현:
  - `openpyxl` 의존성 추가.
  - `extract_spreadsheet_rows` XLSX 추출기 추가.
  - `GangnamExpenseCrawler` 추가: `B_000673` 업무추진비 공개 목록에서 XLSX 첨부 다운로드.
  - `run-agency <agency>` CLI 추가: `seoul_opengov`, `gangnam_xlsx_board` adapter dispatch.
  - `PostRef`/`PostDetail`에 `department_name`, `file_kind`, `content_bytes` 추가.
  - `sources.file_kind`에 실제 `xlsx` 저장되도록 loader 확장.
- Dry-run:
  - 강남구청 1페이지 3개 첨부: `parsed_rows=6`, `kakao_match_rate=100%`.
- 실제 적재:
  - 강남구청 1페이지 10개 첨부 실행.
  - `posts_seen=10`, `posts_fetched=10`, `parsed_rows=6`, `loaded_sources=1`, `loaded_places=5`, `loaded_visits=6`, Kakao match rate `100%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `place_visits=195`, `places_public=161`, 방문 데이터가 있는 기관 `3/52` (`서울시청=175`, `서울시의회=14`, `강남구청=6`).
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 13 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - `npm run build` → passed
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`195`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`3/52`).

## 2026-05-24 구의회 홈페이지 정정 체크포인트

- 발견:
  - 강남구의회 공식 사이트의 서울 시·구 의회 링크 목록에서 25개 구의회 공식 도메인을 확인.
  - 기존 `council.{domain_slug}.go.kr` 추정값은 강남구의회, 강서구의회 등에서 틀림.
- 반영:
  - `SEOUL_COUNCIL_HOMEPAGES` 공식 도메인 매핑 추가.
  - Neon `seed-agencies` 재실행으로 기관 마스터 URL 갱신 완료.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 14 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed

## 2026-05-24 강남구의회 PDF vision 어댑터 체크포인트

- 구현:
  - `GangnamCouncilCrawler` 추가: `https://www.gncouncil.go.kr/kr/noticeBBS.do` 공지 목록에서 업무추진비 PDF 첨부 추출.
  - `extract_pdf_rows_with_vision` 추가: `pdftoppm`으로 PDF를 PNG로 변환 후 Gemini vision 우선, Anthropic fallback.
  - Gemini 응답 JSON fence 파싱을 위해 `_loads_json_response`의 중첩 JSON 처리 수정.
  - council role 텍스트(`구의원 N명`)가 representative 없이 rank만 남도록 마스킹 룰 보강.
  - Kakao keyword match 실패 시 address search로 좌표를 보강하도록 resolver 확장.
  - 강남구의회 `source_pattern.adapter=gncouncil_pdf_board` 반영 후 Neon `seed-agencies` 재실행.
- 품질 확인:
  - Anthropic/Haiku 및 Sonnet의 한 페이지 전체 OCR은 상호명 오인식이 많아 실제 적재에 부적합.
  - Gemini 2.5 Flash compact schema로 전환 후 dry-run 성공:
    - `posts_seen=16`
    - `posts_fetched=1`
    - `parsed_rows=62`
    - `normalized_visits=62`
    - `places_seen=45`
    - `kakao_matched_places=32`
    - Kakao match rate `71.11%`
- 실제 적재:
  - 강남구의회 최신 업무추진비 PDF 1개 실제 적재.
  - `posts_seen=16`, `posts_fetched=1`, `parsed_rows=62`, `loaded_sources=1`, `loaded_places=42`, `loaded_visits=62`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `place_visits=257`, `places_public=203`, 좌표 있는 `places_public=186`, 방문 데이터가 있는 기관 `4/52`.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 19 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - `npm run build` → passed
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`257`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`4/52`).

## 2026-05-24 구의회 첨부 게시판 일반화 + 강서구의회 적재 체크포인트

- 구현:
  - `GangnamCouncilCrawler`를 `CouncilAttachmentCrawler`로 일반화.
  - `listUrl`을 agency `source_pattern`에서 읽도록 변경해 `noticeBBS.do`, `costBBS.do` 계열을 같은 parser로 처리.
  - 첨부 파일명/제목에서 `업무추진비` 또는 `업추비`가 확인되는 `pdf`, `xlsx`만 수집하도록 필터링.
  - 다운로드 링크의 `title`, 이미지 `alt`, 링크 텍스트에서 파일명을 추출하도록 보강.
  - 강북·강서·관악·구로·동작·은평·중랑구의회 `costBBS.do` source_pattern 등록.
  - XLSX extractor 헤더 alias 보강: `가맹점명`, `집행처 명`, `사용금액(원)`, `대상인원(명)`, `사용목적(내역)`, `사용방법` 등.
  - XLSX 주소 컬럼은 `상호명 (주소)` 형태로 deterministic normalizer에 전달해 카카오 매칭 품질을 높임.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 22 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 강서구의회 1개 첨부 dry-run:
    - `parsed_rows=96`
    - `normalized_visits=96`
    - `places_seen=83`
    - Kakao match rate `90.36%`
- 실제 적재:
  - 강서구의회 `2026-01-01` 이후 1페이지 9개 첨부 실행.
  - `posts_seen=9`, `posts_fetched=9`, `parsed_rows=614`, `loaded_visits=614`.
  - Kakao match rate `93.35%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `5/52`, `agency_stats_visit_sum=870`, `places_public=545`, 좌표 있는 `places_public=527`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`870`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`5/52`).

## 2026-05-24 관악구의회 2단 XLSX 헤더 적재 체크포인트

- 구현:
  - XLSX extractor에 2단 헤더 overlay 처리 추가.
  - `집행일시` 하위 `일자/시간`, `집행장소` 하위 `상호명/주소` 구조를 표준 필드로 매핑.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 23 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 관악구의회 1개 첨부 dry-run:
    - `parsed_rows=106`
    - `normalized_visits=106`
    - `places_seen=79`
    - Kakao match rate `94.94%`
- 실제 적재:
  - 관악구의회 `2026-01-01` 이후 1페이지 11개 첨부 실행.
  - `posts_seen=11`, `posts_fetched=11`, `parsed_rows=743`, `loaded_visits=743`.
  - Kakao match rate `92.90%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `6/52`, `agency_stats_visit_sum=1613`, `places_public=863`, 좌표 있는 `places_public=845`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`1613`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`6/52`).

## 2026-05-24 강북구의회 PDF 소량 배치 적재 체크포인트

- 구현:
  - `public-officer-pipeline run-*` 명령에 `--skip-posts` 옵션 추가.
  - PDF vision 추출이 파일별로 흔들릴 때 앞선 성공분을 재처리하지 않고 다음 게시물부터 이어갈 수 있게 함.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 23 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 강북구의회 1개 PDF dry-run:
    - `parsed_rows=48`
    - Kakao match rate `87.80%`
- 실제 적재:
  - 강북구의회 2026년 4월·3월 PDF는 일괄 실행 중 성공해 총 `96`건 적재.
  - 2026년 2월 PDF는 dry-run 성공(`47`건)이지만 실제 실행에서 Gemini JSON 오류가 재발해 보류.
  - 2026년 1월 PDF는 단독 실제 적재 성공: `loaded_visits=47`, Kakao match rate `79.07%`.
  - 2025년 12월 PDF는 dry-run `parsed_rows=0`으로 적재하지 않음.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `7/52`, `agency_stats_visit_sum=1756`, `places_public=973`, 좌표 있는 `places_public=955`.
- 운영 메모:
  - PDF 기관은 일괄 처리보다 `--max-posts 1` + `--skip-posts` 소량 배치가 복구성이 좋음.
  - Gemini vision JSON 오류 파일은 재시도/모델 전환 또는 JSON repair 보강 후 다시 처리.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`1756`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`7/52`).

## 2026-05-24 구로구의회 XLSX 적재 체크포인트

- 구현:
  - XLSX extractor에 `승인금액` 금액 alias 추가.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 24 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 구로구의회 2026년 3월 XLSX dry-run:
    - `parsed_rows=98`
    - `normalized_visits=98`
    - `places_seen=70`
    - Kakao match rate `95.71%`
- 실제 적재:
  - 구로구의회 2026년 3월 XLSX 1개 실제 적재.
  - `loaded_sources=1`, `loaded_places=70`, `loaded_visits=98`.
  - 2026년 4월 PDF는 Gemini JSON 오류로 보류.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `8/52`, `agency_stats_visit_sum=1854`, `places_public=1043`, 좌표 있는 `places_public=1025`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`1854`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`8/52`).

## 2026-05-24 동작구의회 PDF 1개 적재 체크포인트

- 검증:
  - 동작구의회 첫 PDF dry-run:
    - `parsed_rows=85`
    - `normalized_visits=85`
    - `places_seen=66`
    - Kakao match rate `83.33%`
- 실제 적재:
  - 동작구의회 첫 PDF 실제 적재.
  - `loaded_sources=1`, `loaded_places=66`, `loaded_visits=85`.
  - 실제 적재 시 Kakao match rate `84.85%`.
  - 두 번째 PDF는 Gemini JSON 오류로 보류.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `9/52`, `agency_stats_visit_sum=1939`, `places_public=1108`, 좌표 있는 `places_public=1082`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`1939`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`9/52`).

## 2026-05-24 은평·중랑구의회 PDF 1개씩 적재 체크포인트

- 은평구의회:
  - 첫 PDF dry-run: `parsed_rows=77`, Kakao match rate `80.95%`.
  - 실제 적재: `loaded_sources=1`, `loaded_places=57`, `loaded_visits=77`, Kakao match rate `81.25%`.
- 중랑구의회:
  - 첫 PDF dry-run: `parsed_rows=77`, Kakao match rate `88.52%`.
  - 실제 적재: `loaded_sources=1`, `loaded_places=60`, `loaded_visits=77`, Kakao match rate `88.52%`.
- materialized views refresh 완료.
- 직접 DB 확인:
  - `agencies=52`
  - 방문 데이터가 있는 기관 `11/52`
  - `agency_stats_visit_sum=2093`
  - `places_public=1221`
  - 좌표 있는 `places_public=1188`
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`2093`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`11/52`).

## 2026-05-24 동대문구의회 busiexpensesBBS 적재 체크포인트

- 발견:
  - `costBBS.do` 외 추가 게시판명 스캔에서 동대문구의회 `https://council.ddm.go.kr/kr/busiexpensesBBS.do` 확인.
  - PDF 첨부형 업무추진비 게시판으로 기존 `CouncilAttachmentCrawler` 재사용 가능.
- 구현:
  - 동대문구의회 `source_pattern.adapter=council_attachment_board`, `listUrl=.../busiexpensesBBS.do` 추가.
  - Neon `seed-agencies` 재실행 완료.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 24 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 첫 PDF dry-run: `parsed_rows=38`, Kakao match rate `84.38%`.
- 실제 적재:
  - 첫 PDF 실제 적재: `loaded_sources=1`, `loaded_places=32`, `loaded_visits=38`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `12/52`, `agency_stats_visit_sum=2131`, `places_public=1251`, 좌표 있는 `places_public=1213`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`2131`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`12/52`).

## 2026-05-24 송파구의회 상세 첨부 follow 적재 체크포인트

- 발견:
  - 송파구의회 업무추진비 게시판은 `https://council.songpa.go.kr/kr/news/bbsCost.do`.
  - 목록에는 첨부 아이콘만 있고, 실제 `/bbsAttachDownload.do?...` 링크는 상세 페이지에 있음.
- 구현:
  - `CouncilAttachmentCrawler`에 `followDetail` 모드 추가.
  - 목록 row에서 상세 URL·제목·작성일을 추출하고, 상세 페이지에서 첨부 다운로드 링크를 다시 추출.
  - `bbsAttachDownload.do` 링크와 `YYYY.MM.DD` 날짜 포맷 지원.
  - 송파구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - Neon `seed-agencies` 재실행 완료.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 25 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 첫 PDF dry-run: `parsed_rows=23`, Kakao match rate `90.48%`.
  - 두 번째 PDF dry-run: `parsed_rows=23`, Kakao match rate `85.00%`.
- 실제 적재:
  - 첫 PDF 실제 적재: `loaded_visits=23`.
  - 두 번째 PDF 실제 적재: `loaded_visits=23`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `13/52`, `agency_stats_visit_sum=2177`, `places_public=1289`, 좌표 있는 `places_public=1246`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`2177`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`13/52`).

## 2026-05-24 마포구의회 followDetail + PDF JSON repair 체크포인트

- 발견:
  - 마포구의회 업무추진비 게시판은 `https://council.mapo.seoul.kr/kr/news/bbsCost.do`.
  - 목록에는 상세 링크만 있고, 상세 페이지의 `/bbsAttachDownload.do?...` 아래 PDF 첨부를 내려받아야 함.
- 구현:
  - 마포구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - Gemini vision PDF 추출 호출에 `responseMimeType=application/json` 적용.
  - LLM JSON 응답의 흔한 쉼표 누락(`}{`, 줄바꿈 뒤 다음 key)을 실패 후 보정하도록 `_loads_json_response` 보강.
  - 관련 테스트 추가 및 기관 스냅샷 테스트 갱신.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` → 26 passed
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` → passed
  - 마포구의회 첫 PDF dry-run: `parsed_rows=9`, Kakao match rate `87.50%`.
- 실제 적재:
  - 마포구의회 최신 월 5개 PDF 실제 적재 완료.
  - 중간 Gemini JSON 오류 후 repair/retry 보강으로 실패 PDF 재처리 성공.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `14/52`, `agency_stats_visit_sum=2322`, `places_public=1386`, 좌표 있는 `places_public=1323`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`2322`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`14/52`).

## 2026-05-24 금천구의회 4열 첨부 테이블 + 텍스트 PDF 적재 체크포인트

- 발견:
  - 금천구의회 업무추진비 게시판은 `https://council.geumcheon.go.kr/council/kr/costBBS.do`.
  - 목록 페이지가 4열 구조라 기존 `CouncilAttachmentCrawler`의 6열 테이블 가정으로는 0건 반환.
  - 금천 PDF는 `Microsoft Print To PDF` 텍스트 기반이라 vision보다 `pdftotext -layout` 파싱이 안정적.
- 구현:
  - 금천구의회 `source_pattern.adapter=council_attachment_board` 등록.
  - `CouncilAttachmentCrawler._parse_list`를 4열 이상 + 마지막 셀 첨부 기준으로 완화.
  - PDF 처리 앞단에 `pdftotext -layout` 기반 `rows_from_pdf_text`를 추가하고, 텍스트 row가 잡히면 vision 호출 없이 반환.
  - 금천 4열 테이블/텍스트 PDF parser 테스트 추가.
- 검증:
  - 금천구의회 두 번째 PDF dry-run: `parsed_rows=13`, Kakao match rate `92.31%`.
  - 타깃 테스트: `13 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 금천구의회 최신 페이지 12개 첨부 실제 적재.
  - `posts_seen=12`, `posts_fetched=12`, `parsed_rows=505`, `loaded_visits=505`, Kakao match rate `69.70%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `15/52`, `agency_stats_visit_sum=2823`, `places_public=1447`, 좌표 있는 `places_public=1363`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`2823`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`15/52`).

## 2026-05-24 도봉구의회 followDetail XLSX 적재 체크포인트

- 발견:
  - 도봉구의회 업무추진비 게시판은 `https://www.council-dobong.seoul.kr/kr/activity/bbsCost.do`.
  - 목록은 상세 링크만 제공하고, 상세 페이지에서 `/bbsAttachDownload.do?...` XLSX/PDF 첨부를 내려받아야 함.
  - 최신 분기 XLSX는 다중 시트 구조이며 헤더가 `상호`, `인원수`, `구분`처럼 짧은 명칭을 사용.
- 구현:
  - 도봉구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - spreadsheet extractor 헤더 alias에 `상호`, `인원수`, `구분` 추가.
  - 도봉식 XLSX 헤더 테스트 추가.
- 검증:
  - 도봉구의회 최신 XLSX dry-run: `parsed_rows=474`, Kakao match rate `60.45%`.
  - 타깃 테스트: `10 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 도봉구의회 최신 페이지 7개 첨부 실행.
  - 최신 분기 XLSX 1개에서 `loaded_visits=474`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `16/52`, `agency_stats_visit_sum=3297`, `places_public=1610`, 좌표 있는 `places_public=1443`.
- 운영 메모:
  - 같은 페이지의 월별 의회사무국 XLSX는 현재 parser 기준 0건으로 처리됨. 별도 구조 확인 후 추가 보강 가능.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`3297`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`16/52`).

## 2026-05-24 서초구의회 purpose-first PDF 적재 체크포인트

- 발견:
  - 서초구의회 업무추진비 게시판은 `https://www.sdc.seoul.kr/kr/news/bbsBusiness.do`.
  - 상세 페이지의 `/bbsAttachDownload.do?...` PDF 첨부를 따라가야 함.
  - PDF 텍스트 표는 컬럼 순서가 `목적 → 지출금액 → 결제방법 → 장소 → 대상인원수`라 금천식 텍스트 parser가 목적을 장소로 오인해 Kakao match rate `0%` 발생.
- 구현:
  - 서초구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - `rows_from_pdf_text`에 purpose-first PDF row parser 추가.
  - `부의장` 파일명이 `의장`보다 먼저 분류되도록 department 추론 순서 수정.
  - purpose-first parser 및 부의장 분류 테스트 추가.
- 검증:
  - 보강 후 서초구의회 최신 PDF dry-run: `parsed_rows=30`, Kakao match rate `83.33%`.
  - 타깃 테스트: `15 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 서초구의회 최신 페이지 20개 PDF 실제 적재.
  - `posts_seen=20`, `posts_fetched=20`, `parsed_rows=350`, `loaded_visits=350`, Kakao match rate `92.19%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `17/52`, `agency_stats_visit_sum=3647`, `places_public=1780`, 좌표 있는 `places_public=1600`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`3647`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`17/52`).

## 2026-05-24 용산구의회 direct attachment PDF 적재 체크포인트

- 발견:
  - 용산구의회 업무추진비 게시판은 `https://www.yscl.go.kr/kr/councilcostBBS.do`.
  - 목록 페이지 마지막 첨부 셀에 `/kr/bbs/download.do?bbs_id=councilcost...` PDF 링크가 직접 노출됨.
  - 기존 `CouncilAttachmentCrawler`의 직접 첨부 목록 파서로 처리 가능.
- 구현:
  - 용산구의회 `source_pattern.adapter=council_attachment_board` 등록.
  - 기관 스냅샷 테스트 갱신.
- 검증:
  - 용산구의회 최신 PDF dry-run: `parsed_rows=13`, Kakao match rate `81.82%`.
  - 타깃 테스트: `15 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 용산구의회 최신 페이지 29개 PDF 실제 적재.
  - `posts_seen=29`, `posts_fetched=29`, `parsed_rows=385`, `loaded_visits=385`, Kakao match rate `84.93%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `18/52`, `agency_stats_visit_sum=4031`, `places_public=1973`, 좌표 있는 `places_public=1762`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`4031`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`18/52`).

## 2026-05-24 강동구의회 followDetail PDF 적재 체크포인트

- 발견:
  - 강동구의회 업무추진비 게시판은 `https://council.gangdong.go.kr/kr/news/bbsBusiness.do`.
  - 목록은 상세 링크만 제공하고, 상세 페이지에서 `/bbsAttachDownload.do?...` 단일 PDF 첨부를 내려받는 구조.
- 구현:
  - 강동구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - 기관 스냅샷 테스트 갱신.
- 검증:
  - 강동구의회 최신 PDF dry-run: `parsed_rows=117`, Kakao match rate `90.22%`.
  - 타깃 테스트: `15 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 강동구의회 최신 페이지 5개 PDF 실제 적재.
  - `posts_seen=5`, `posts_fetched=5`, `parsed_rows=322`, `loaded_visits=322`, Kakao match rate `89.91%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `19/52`, `agency_stats_visit_sum=4348`, `places_public=2179`, 좌표 있는 `places_public=1946`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`4348`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`19/52`).

## 2026-05-24 성북구의회 followDetail user-address PDF 적재 체크포인트

- 발견:
  - 성북구의회 업무추진비 게시판은 `https://www.sbc.go.kr/kr/news/bbsCost.do`.
  - 목록은 상세 링크만 제공하고, 상세 페이지에서 `/bbsAttachDownload.do?...` PDF 첨부를 내려받는 구조.
  - PDF 텍스트 표는 `사용자 → 사용일 → 사용시간 → 집행장소 → 주소 → 집행목적 → 인원 → 금액 → 결제방법 → 비목` 순서라 기존 금천/서초 PDF parser로는 0건.
- 구현:
  - 성북구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - `rows_from_pdf_text`에 user-address PDF row parser 추가.
  - 기관 스냅샷 및 성북식 PDF 텍스트 parser 테스트 추가.
- 검증:
  - 성북구의회 최신 PDF 텍스트 단위 추출: `rows=171`.
  - 성북구의회 최신 PDF dry-run: `parsed_rows=171`, Kakao match rate `87.69%`.
  - 타깃 테스트: `11 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 성북구의회 최신 페이지 5개 PDF 실제 적재.
  - `posts_seen=5`, `posts_fetched=5`, `parsed_rows=631`, `loaded_visits=631`, Kakao match rate `90.43%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `20/52`, `agency_stats_visit_sum=4962`, `places_public=2472`, 좌표 있는 `places_public=2239`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`4962`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`20/52`).

## 2026-05-24 광진구의회·양천구의회 bbs_process PDF 적재 체크포인트

- 발견:
  - 광진구의회 업무추진비 게시판은 `https://council.gwangjin.go.kr/kr/data/bbs?bbs_id=businesswork`.
  - 양천구의회 업무추진비 게시판은 `https://www.ycc.go.kr/kr/news/bbs?bbs_id=business`.
  - 두 사이트 모두 목록 → 상세 → `bbs_process?reform=download` PDF 다운로드 구조.
  - 기존 crawler가 `listUrl`의 query string을 보존하지 않고 `page` param만 보내 `bbs_id`가 사라지는 문제가 있었음.
- 구현:
  - `CouncilAttachmentCrawler`가 기존 query string을 보존하며 `page`만 추가하도록 수정.
  - `bbs_process?reform=download` 다운로드 링크 지원 추가.
  - 광진/양천 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - 광진식 주소 없는 PDF row parser 추가 및 1월/2월 변형(행번호 없음, 목적 시작어 차이) 보강.
  - 양천식 `장소 → 금액 → 목적 → 인원 → 결제방법` PDF row parser 추가.
- 검증:
  - 광진구의회 실제 목록 probe: 2026년 PDF 10개 감지.
  - 양천구의회 실제 목록 probe: 2026년/2025년 4개 업무추진비 PDF 감지.
  - 광진 최신 PDF dry-run: `parsed_rows=69`, Kakao match rate `93.22%`.
  - 양천 최신 PDF dry-run: `parsed_rows=101`, Kakao match rate `94.20%`.
  - 타깃 테스트: `20 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 광진구의회 최신 페이지 10개 PDF 실제 적재.
  - `posts_seen=10`, `posts_fetched=10`, `parsed_rows=436`, `loaded_visits=436`, Kakao match rate `93.82%`.
  - 양천구의회 최신 페이지 4개 PDF 실제 적재.
  - `posts_seen=4`, `posts_fetched=4`, `parsed_rows=350`, `loaded_visits=350`, Kakao match rate `25.39%`.
  - 양천은 PDF에 주소가 없어 분기 전체 실행 기준 상호명만으로 resolve되며 fallback place 비율이 높음.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `22/52`, `agency_stats_visit_sum=5746`, `places_public=2951`, 좌표 있는 `places_public=2511`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`5746`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`22/52`).

## 2026-05-24 서대문구의회 CP949 XLS 적재 체크포인트

- 발견:
  - 서대문구의회 업무추진비 게시판은 `https://www.sdmcouncil.go.kr/source/korean/partake/business.html`.
  - HTML 응답은 CP949/EUC-KR 계열이라 기본 decode 시 한글이 깨져 목록 title keyword matching이 실패.
  - 상세 페이지에서 `/Mboard/download.html?...` `.xls` 파일을 제공하며, 기존 `openpyxl`은 OLE XLS를 읽지 못함.
  - DB `sources.file_kind` check constraint가 `xls`를 허용하지 않아 첫 실제 적재가 실패.
- 구현:
  - `CouncilAttachmentCrawler`에 CP949 fallback decode 추가.
  - `/Mboard/download.html` 다운로드 링크 및 `xls` file kind 지원 추가.
  - `xlrd` 의존성 추가 후 OLE `.xls` reader 구현.
  - 서대문 XLS 헤더(`집행일`, `집행인원`, `집행액(천원)`)와 중복 `집행유형` 목적/결제방법 disambiguation 보강.
  - `sources.file_kind`에 `xls`를 허용하는 migration 추가 및 Neon 적용.
  - 서대문구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
- 검증:
  - 서대문구의회 실제 목록 probe: `posts=7`.
  - 최신 XLS 단위 추출: `rows=78`.
  - dry-run: `parsed_rows=78`, Kakao match rate `95.24%`.
  - 타깃 테스트: `19 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 서대문구의회 최신 페이지 7개 XLS 실제 적재.
  - `posts_seen=7`, `posts_fetched=7`, `parsed_rows=235`, `loaded_visits=235`, Kakao match rate `96.43%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `23/52`, `agency_stats_visit_sum=5981`, `places_public=3064`, 좌표 있는 `places_public=2620`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`5981`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`23/52`).

## 2026-05-24 중구의회 extensionless download PDF 적재 체크포인트

- 발견:
  - 중구의회 업무추진비 게시판은 `https://council.junggu.seoul.kr/kr/bbs?bbs_id=cost`.
  - 목록 → 상세 → `/kr/bbs/download?...` PDF 다운로드 구조이며, 확장자 없는 download path라 기존 `/bbs/download.do` 패턴으로는 미감지.
  - PDF 텍스트 표는 `승인일 → 승인시각 → 사용자 → 금액 → 장소 → 집행목적 → 대상인원수 → 결제방법 → 비목` 순서라 양천식 parser가 장소를 사용자로 오인.
- 구현:
  - `CouncilAttachmentCrawler`에 `/bbs/download?` 다운로드 링크 지원 추가.
  - 중구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - 중구식 `date/user/amount/place` PDF row parser 추가.
- 검증:
  - 중구의회 실제 목록 probe: `posts=5`.
  - 최신 PDF 단위 추출: `rows=91`.
  - dry-run: `parsed_rows=91`, Kakao match rate `90.48%`.
  - 타깃 테스트: `23 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 중구의회 최신 페이지 5개 PDF 실제 적재.
  - `posts_seen=5`, `posts_fetched=5`, `parsed_rows=406`, `loaded_visits=406`, Kakao match rate `90.74%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `24/52`, `agency_stats_visit_sum=6387`, `places_public=3255`, 좌표 있는 `places_public=2791`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`6387`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`24/52`).

## 2026-05-25 종로구의회 eGov FileDown PDF 적재 체크포인트

- 발견:
  - 종로구의회 업무추진비 게시판은 `https://council.jongno.go.kr/council/bbs/BBSMSTR_000000000061/list.do?menuNo=401070`.
  - 목록은 table row가 아니라 `view.do?nttId=...` 링크 목록으로 렌더링되어 기존 `tbody tr` parser로는 0건.
  - 첨부는 상세 페이지의 `/portal/cmm/fms/FileDown.do?...` PDF 다운로드 구조.
  - PDF 텍스트 표는 `사용자 → 사용일시 → 거래처명 → 집행목적 → 사용금액 → 대상인원수 → 사용방법` 순서이며, 거래처명 중간에 지점명이 공백으로 포함됨.
- 구현:
  - `CouncilAttachmentCrawler._parse_detail_links`에 table 없는 eGov `view.do` 링크 fallback 추가.
  - `/FileDown.do` 다운로드 링크 및 `pdf [size]` 파일명 확장자 감지 지원 추가.
  - 종로구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - 종로식 `user/place/purpose/amount` PDF row parser 추가.
- 검증:
  - 종로구의회 실제 목록 probe: `posts=20`.
  - 최신 PDF 단위 추출: `rows=92`.
  - dry-run: `parsed_rows=92`, Kakao match rate `91.80%`.
  - 타깃 테스트: `25 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 종로구의회 2026년 최신 4개 PDF 실제 적재.
  - `posts_seen=20`, `posts_fetched=4`, `parsed_rows=362`, `loaded_visits=362`, Kakao match rate `88.56%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `25/52`, `agency_stats_visit_sum=6748`, `places_public=3430`, 좌표 있는 `places_public=2943`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`6748`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`25/52`).

## 2026-05-25 성동구의회·영등포구의회 PDF 적재 체크포인트

- 발견:
  - 성동구의회 업무추진비 게시판은 `https://sdcouncil.sd.go.kr/kr/data/bbs?bbs_id=expenses`.
  - 성동 상세 페이지는 `/kr/data/bbs_process?reform=download...` PDF 첨부 구조이며, 제목에 `시책추진비`만 있는 의회사무국 파일도 실제 업무추진비 PDF를 제공.
  - 영등포구의회 업무추진비 게시판은 `https://www.ydpc.go.kr/content/news/bbsCost.html`.
  - 영등포 상세 페이지는 `/gtb_download.php?gtid=work&fid=...` PDF 첨부 구조.
  - 두 기관 모두 text-based PDF지만 표 순서가 달라 기존 parser가 집행목적을 장소로 오인하거나 0행 처리.
- 구현:
  - 성동구의회·영등포구의회 `source_pattern.adapter=council_attachment_board`, `followDetail=true` 등록.
  - `CouncilAttachmentCrawler`에 `/gtb_download.php` 다운로드 링크 지원 추가.
  - 제목 키워드에 `시책추진비` 추가.
  - 성동식 `purpose/place/amount`, `region/amount/place/purpose` PDF row parser 추가.
  - 영등포식 `optional user/place/purpose/amount`, `user/amount/place/address/purpose` PDF row parser 추가.
- 검증:
  - 성동구의회 실제 목록 probe: `posts=4`.
  - 성동 dry-run: `parsed_rows=563`, Kakao match rate `93.38%`.
  - 영등포구의회 실제 목록 probe: `posts=7`.
  - 영등포 dry-run: `parsed_rows=306`, Kakao match rate `88.65%`.
  - 타깃 테스트: `31 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 성동구의회 2026년 1분기 PDF 2개 실제 적재.
  - `posts_seen=4`, `posts_fetched=2`, `parsed_rows=563`, `loaded_visits=563`, Kakao match rate `93.38%`.
  - 영등포구의회 2026년 최신 PDF 5개 실제 적재.
  - `posts_seen=7`, `posts_fetched=5`, `parsed_rows=345`, `loaded_visits=345`, Kakao match rate `75.75%`.
  - materialized views refresh 완료.
  - 직접 DB 확인: `agencies=52`, 방문 데이터가 있는 기관 `27/52`, `agency_stats_visit_sum=7656`, `places_public=3937`, 좌표 있는 `places_public=3367`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`7656`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`27/52`).
  - 의회 중 노원구의회는 확인한 최신 XLS에 장소/가맹점 컬럼이 없어 식당 지도 데이터로는 보류.

## 2026-05-25 관악구청 HTML estimateList 부분 적재 체크포인트

- 발견:
  - 관악구청 업무추진비 공개 페이지는 `https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do`.
  - 첨부파일이 아니라 `table.view` key-value 테이블 10개가 페이지마다 직접 렌더링됨.
  - 2026-01-01 이후 필터 기준 공개 건수는 `6,145`건이며, pageIndex 기반 페이지네이션.
- 구현:
  - `EstimateListCrawler` 추가: `pageIndex`, `searchCondition3`, `searchCondition4` 쿼리로 날짜 필터 페이지를 PostRef로 생성.
  - `extract_expense_rows`에 key-value `th/td` 업무추진비 테이블 파서 추가.
  - 관악구청 `source_pattern.adapter=estimate_list_html` 등록.
  - DB agency master 재시드 완료.
- 검증:
  - 관악구청 5페이지 dry-run: `parsed_rows=50`, Kakao match rate `91.67%`.
  - 타깃 테스트: `11 passed`
  - 타깃 `ruff check` → passed
- 실제 적재:
  - 20페이지 배치를 실행했으나 카카오 매칭 지연으로 중단.
  - 페이지 단위 loader commit 결과 17개 페이지가 적재됨.
  - 직접 DB 확인: 관악구청 `visit_count=169`, `place_count=134`.
  - 전체 DB 확인: 방문 데이터가 있는 기관 `28/52`, `agency_stats_visit_sum=7825`, `places_public=4026`, 좌표 있는 `places_public=3456`.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준은 아직 미달 (`7825`).
  - `>=45/52` 기관 적재 기준은 아직 미달 (`28/52`).
  - 다음 관악 배치는 `--skip-posts 17` 이후 5~10페이지 단위로 진행 필요.

## 2026-05-25 구청 첨부 게시판 확장 체크포인트

- 구현:
  - 구청용 `attachment_board` adapter alias 등록.
  - 강동구청 `b_054`, 금천구청 `bbsNo=86`, 동대문구청 `bbsNo=160`, 서초구청 `cbIdx=33`, 구로구청 `bbsNo=655` 소스 패턴 등록.
  - `downloadBbsFile.do`, `downloadBbsFileStr.do`, `/file/download/`, `/common/board/Download.do` 첨부 링크 지원.
  - 강동구청식 텍스트 PDF 파서 추가: `YYYYMMDD` 날짜, 빈 줄로 쪼개진 행, 인원/금액/결제방식 세그먼트 처리.
  - 텍스트 PDF는 `pdftotext -layout` 실패 시 plain `pdftotext`로 재시도.
  - DB 실명 잔존 방지를 위해 normalized visit의 `raw_excerpt`를 빈 문자열로 강제하고, 기존 DB `raw_excerpt`도 전부 빈 문자열로 정리.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` -> 57 passed.
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` -> passed.
  - 강동구청 dry-run 1건: `parsed_rows=13`, Kakao match rate `91.67%`.
  - 금천구청 dry-run 1건: `parsed_rows=8`, Kakao match rate `100%`.
  - 서초구청 dry-run 1건(skip 8): `parsed_rows=1`, Kakao match rate `100%`.
  - 동대문구청 dry-run 1건: `parsed_rows=6`, Kakao match rate `0%`라 품질 개선 필요.
- 실제 적재:
  - 강동구청은 장시간 배치를 중단했지만 post 단위 적재로 6개 source, 39 visits 적재됨.
  - 금천구청 1개 source, 8 visits 적재.
  - 동대문구청 1개 source, 6 visits 적재.
  - 서초구청 1개 source, 1 visit 적재.
  - refresh 후 집계: `52 agencies`, 방문 데이터 기관 `32/52`, 총 visits `7,879`.
  - `raw_excerpt <> ''` 잔여 row: `0`.
- 주의:
  - 구로구청은 직접 PDF 첨부 추출은 되지만 최신 PDF가 현행 텍스트 파서에서 느린 vision 경로로 빠져 실제 적재 보류.
  - Phase 2 기준은 아직 실패: `place_visits > 10,000` 미달, `>=45/52` 미달.

## 2026-05-25 마포·송파·양천 구청 소스 확장 체크포인트

- 구현:
  - 마포구청 `https://www.mapo.go.kr/site/main/board/expense/list` 소스 등록.
  - 송파구청 `https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=327&key=2323` 소스 등록.
  - 양천구청 `https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397` 소스 등록.
  - 양천구청 `doBbsFView(...)` JavaScript 상세 링크와 `wdigm_title(...)` 제목 파싱 지원 추가.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` -> 58 passed.
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` -> passed.
  - Neon materialized views refresh 완료.
  - 직접 DB 확인: `52 agencies`, 방문 데이터가 있는 기관 `34/52`, 총 visits `7,910`.
  - `raw_excerpt` 잔여 row: `0`.
- 실제 적재:
  - 송파구청 1개 source, 21 visits, 18 places 적재.
  - 마포구청 1개 source, 10 visits, 10 places 적재.
  - 양천구청은 최신 XLSX dry-run에서 `parsed_rows=0`이라 소스 등록과 상세 링크 파싱만 반영, 실제 적재 보류.
- 남은 Phase 2 실패:
  - `place_visits > 10,000` 기준 미달 (`7,910`).
  - `>=45/52` 기관 적재 기준 미달 (`34/52`).

## 2026-05-25 성동·강서 구청 적재 및 노원 소스 등록 체크포인트

- 구현:
  - 성동구청 `https://sd.go.kr/main/selectBbsNttList.do?bbsNo=172&key=1330` 소스 등록.
  - 강서구청 `https://www.gangseo.seoul.kr/gs030325` 소스 등록 및 상세 페이지 첨부 follow 지원.
  - 노원구청 `https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1012` 소스 등록.
  - `/component/file/ND_fileDownload.do`, `/comm/getFile` 다운로드 링크 지원.
  - 목록의 공표부서 셀에서 부서명을 추출하도록 `attachment_board` 보강.
  - 성동구청식 `pdftotext -layout` 컬럼형 PDF 파서 추가.
  - 주소 없는 구청/구의회 식당명에 `서울 {자치구}` 지역 힌트를 보강하도록 deterministic normalizer 수정.
- 검증:
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest` -> 62 passed.
  - `uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check` -> passed.
  - Neon materialized views refresh 완료.
  - 직접 DB 확인: `52 agencies`, 방문 데이터가 있는 기관 `36/52`, 총 visits `7,947`.
- 실제 적재:
  - 성동구청 1개 source, 26 visits 적재.
  - 강서구청 2개 source, 11 visits 적재.
  - 노원구청은 공식 목록과 다운로드 URL 등록은 완료했지만 최신 XLSX/PDF가 현 파서에서 `parsed_rows=0` 또는 vision 경로로 빠져 실제 적재 보류.
- 주의:
  - 현재 로컬 셸에는 `KAKAO_REST_KEY`가 없어 신규 적재분은 fallback place로 적재됨. 좌표 재매칭은 키 주입 후 별도 보강 필요.
  - Phase 2 기준은 아직 실패: `place_visits > 10,000` 미달, `>=45/52` 미달.
