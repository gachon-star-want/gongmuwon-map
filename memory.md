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
