# RUNBOOK — 자율 모드 실행 순서

이 문서는 **자율 에이전트가 부팅 시 가장 먼저 읽는 운영 가이드**입니다. 단계별로 정확히 따르고, 각 단계 끝에 셀프 체크리스트로 검증한 뒤 다음 단계로 넘어가십시오.

## 전제 조건

### 이미 완료된 것 (사용자가 사전 준비)
- ✅ **Neon CLI 로그인** (`neonctl auth`) 완료 — DB 스택 ([ADR-010](adr/ADR-010-database-stack-migration.md))
- ✅ **Cloudflare 계정 + R2 활성화** — Object Storage
- ✅ **Vercel CLI 로그인** (`vercel login`) 완료, 프로젝트 이미 연결됨
- ✅ **GitHub CLI 로그인** (`gh auth status` 확인 완료), 저장소 + 도메인 이미 설정됨
- ✅ **외부 API 키** — 사용자가 직접 마련, 배포 직전 환경변수로 주입
  - **DB**: `DATABASE_URL` (Neon, service 쓰기용), `DATABASE_URL_READONLY` (Neon `anon` RLS-restricted)
  - **R2**: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET=officer-map-raw`
  - **LLM 3종**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (멀티 프로바이더 라우팅 — [ADR-009](adr/ADR-009-multi-llm-provider-routing.md))
  - **카카오**: `KAKAO_JS_KEY` (도메인 제한), `KAKAO_REST_KEY` (Vercel API Route 서버 측 전용)
  - **메일**: `RESEND_API_KEY`
  - **라우팅 설정**: `LLM_PRIMARY=anthropic`, `LLM_FALLBACK_ORDER=openai,gemini,anthropic-sonnet`, `LLM_BUDGET_DAILY_USD=10`

### 자율 모드 시작 전 사용자가 마지막으로 채울 것

| 항목 | 어디 | 비고 |
|---|---|---|
| 운영자 실명/단체명·이메일·연락처·주소 | `AGENTS.md` 끝, `LEGAL_PRIVACY.md`, `UI_UX.md` 푸터 | 정통망법 의무 |
| 도메인 (구입 또는 결정) | DNS 설정 + `vercel.json` | `ADR-007` |

### 자율 모드가 CLI로 직접 처리할 것

| 작업 | 명령 |
|---|---|
| Neon 프로젝트 생성 | `neonctl projects create gongmuwon-map --org-id <org>` → `DATABASE_URL` 획득 |
| Neon 역할 생성 (1회) | `public-officer-pipeline apply-schema`가 `anon`, `authenticated`, `service_role` NOLOGIN 역할을 idempotent하게 생성 |
| Cloudflare R2 버킷 생성 | 대시보드에서 `officer-map-raw` 버킷 + API 토큰 발급 (R2 SDK 사용) |
| Vercel 프로젝트 연결 확인 | (이미 연결됨) `vercel link` — 재실행 불필요 |
| GitHub 저장소 push | (이미 생성됨) `git push origin main` |
| GitHub Secret 주입 | `gh secret set DATABASE_URL`, `gh secret set R2_ACCESS_KEY_ID` 등 |
| Vercel 환경변수 주입 | `vercel env add DATABASE_URL production`, `vercel env add R2_ACCOUNT_ID production` 등 |

미확정 운영자 토큰이 모든 MD에 남아 있는지 시작 시 grep으로 확인: `grep -rn '<<''TBD' --include='*.md'`. 0건이어야 자율 모드 Phase 1 진입 가능.

## Phase 0: 운영자 정보 채우기 (자율 모드 시작 직후, 약 5분)

자율 에이전트는 Phase 1 시작 전에 사용자에게 다음 6개 값을 묻고, 모든 MD의 운영자 미확정 토큰을 자동 치환한다.

| 필드 | 예시 |
|---|---|
| `OPERATOR_NAME` | "이원영" 또는 "공무원맵 운영팀" |
| `OPERATOR_EMAIL` | `admin@gongmuwon-map.com` |
| `OPERATOR_PHONE` | `+82-10-xxxx-xxxx` |
| `OPERATOR_ADDRESS` | "서울시 ○○구 ○○로 ..." (가처분 송달 가능 주소) |
| ~~`OPERATOR_BIZ_NO`~~ | **사전 확정: "(해당 없음)" — 개인 운영** |
| `DOMAIN_PRIMARY` | `gongmuwon-map.com` — 영문, canonical/메일/API ([ADR-007](adr/ADR-007-deployment-strategy.md)) |
| `DOMAIN_ALIAS` | `xn--v69ak0xskm.com` (= `공무원맵.com`) — 사용자 입구, 영문으로 301 redirect. 미사용 시 `(없음)` |

치환 명령 (자율 에이전트 실행):
```bash
# 예시 (실제 값은 사용자 응답으로 받아 치환)
sed -i '' 's|운영자정보_미확정|이원영 · admin@... · ...|g' AGENTS.md
sed -i '' 's|운영자명_미확정|이원영|g' docs/LEGAL_PRIVACY.md
sed -i '' 's|운영자이메일_미확정|admin@gongmuwon-map.com|g' docs/LEGAL_PRIVACY.md docs/UI_UX.md
# 등 ... 자율 에이전트가 grep 결과를 보고 일괄 처리
```

치환 후 검증: `grep -rn '<<''TBD' --include='*.md'` 결과 0건.

**자기 참조 4곳 예외**(검증 시그널이라 변경 금지):
- `RUNBOOK.md` L18 (자기 참조)
- `RUNBOOK.md` Phase 3 체크리스트 (운영자 미확정 토큰 grep 결과 0건)
- `TEST_PLAN.md` 수동 QA 항목 (운영자 미확정 토큰 grep 결과 0건)

이 4곳은 코드 블록 안 또는 백틱 문구로 표시되어 있어 자동 치환 대상에서 제외 가능.

## Phase 1: 파이프라인 + 첫 데이터 (약 90분)

**목표**: 서울시청 단일 소스에서 최근 1개월 데이터를 끝까지 적재.

### 1.1 저장소 구조 부트스트랩
- `apps/web/` Vite + React + TypeScript + Mantine 스캐폴드
- `api/` Vercel API Routes (Node.js/TypeScript) — 프론트와 동일 Vercel 프로젝트 ([ADR-010](adr/ADR-010-database-stack-migration.md))
- `services/pipeline/` Python 3.12 + uv 또는 poetry 환경
- `supabase/migrations/20260523235106_initial.sql` — `DATA_MODEL.md` SQL 그대로 (파일 경로는 commit 히스토리 보존을 위해 유지, Neon에 적용)

### 1.2 Neon 스키마 적용
- Neon 역할 생성은 마이그레이션 상단의 role bootstrap 블록이 idempotent하게 처리한다.
- 마이그레이션 적용: `uv run --project services/pipeline public-officer-pipeline apply-schema` (내부에서 `DATABASE_URL`로 SQL 실행)
- RLS·뷰·SQL 함수 생성 확인
- `place_grade_v1` 머티리얼라이즈드 뷰 빈 상태로 생성

### 1.3 Crawler 어댑터 1개 (서울시청)
- 서울 정보소통광장 `expense/list` HTML 표 파서
- `agencies` 테이블에 `seoul_city_hall` 시드

### 1.4 Extractor·Normalizer
- HTML 표 → 자유 텍스트 변환
- `LLMClient.extract(task=TABLE_NORMALIZE, ...)` 호출 (1차 Gemini 3.5 Flash, [ADR-009](adr/ADR-009-multi-llm-provider-routing.md) 라우팅), 정규화 JSON 받기
- 마스킹 검증 (`LLMClient.extract(task=MASKING_VERIFY, ...)` — Claude Sonnet 4.6 + ET 16K)

### 1.5 Entity Resolver·Geocoder
- 카카오 로컬 검색 API 호출, placeId·좌표 획득
- 폴백 자연키 생성 로직 검증

### 1.6 Loader
- Neon Postgres에 직접 SQL upsert (psycopg/asyncpg, `DATABASE_URL` service role)
- 원본 파일은 Cloudflare R2(`officer-map-raw` 버킷)에 업로드 → `sources.storage_path = r2://...`
- 멱등성 테스트(같은 sample 두 번 실행해도 row 수 동일)

### 1.7 등급 계산
- Vercel API Route `/api/cron/recompute-grades` 호출 (수동: `curl https://<vercel-url>/api/cron/recompute-grades`)
- `places_public` 뷰에서 grade 컬럼 채워지는지 확인

### Phase 1 셀프 체크리스트
- [ ] `place_visits`에 100+ rows
- [ ] `places`에 30+ rows (식당 수)
- [ ] 모든 row의 `representative` 컬럼이 NULL이거나 시장 직급
- [ ] `places_public` 뷰가 `DATABASE_URL_READONLY` (Neon anon role) 로 SELECT 가능
- [ ] `place_grade_v1`에 grade가 채워진 row 다수
- [ ] 카카오 로컬 매칭율 ≥ 70%

## Phase 2: 프론트 MVP + 나머지 51개 소스 백필 (약 120분)

**목표**: 사용자가 지도에서 데이터를 볼 수 있는 첫 페이지 + 데이터 풀 적재.

### 2.1 카카오맵 SDK 통합
- `index.html`에 SDK 스크립트 (도메인 제한 키)
- 마커 클러스터링 라이브러리 추가
- 등급별 마커 컴포넌트

### 2.2 Mantine 레이아웃
- 헤더·필터 바·디테일 패널·바텀시트 (모바일)
- 다크모드·다국어 베이스

### 2.3 API 클라이언트
- 자체 Vercel API Routes (`/api/v1/places`, `/api/v1/places/[id]`, `/api/v1/agencies` 등) 호출 — 클라이언트는 DB 자격 증명 없이 fetch만
- TanStack Query 훅: `usePlaces(bbox, filters)`, `usePlace(id)`, `usePlaceVisits(id)`

### 2.4 SEO 베이스
- path별 메타태그 JS 동적 주입
- Vercel API Route `/api/sitemap` (Vercel Cron이 매일 워밍) — sitemap.xml + llms.txt 동적 응답
- JSON-LD Restaurant 스키마

### 2.5 나머지 51개 기관 백필
- LLM 기반 generic adapter로 각 자치구청·의회 게시판 어댑팅
- 실패율 > 30% 기관은 GitHub Issue 생성 → v1.1로 미룸
- 24개월 백필 실행 (등급 계산은 12개월만 사용)

### 2.6 노티스앤테이크다운 + 폐업 신고 Vercel API Routes
- `POST /api/takedown-request` (구 `notice-takedown`): 폼 접수 → 즉시 hide → 운영자 이메일 (Resend SDK)
- `POST /api/closure-report` (구 `closure-report`): 누적 3건 시 자동 폐업 (SQL 함수 `report_closure` 호출)
- `vercel deploy` 한 번으로 프론트와 동시 배포

### Phase 2 셀프 체크리스트
- [ ] localhost:5173에서 지도 + 마커 + 디테일 패널 동작
- [ ] 필터 4종(자치구·등급·기관 유형·검색) 동작
- [ ] 모바일 뷰포트에서 바텀시트 동작
- [ ] `place_visits` row > 10,000
- [ ] 적재된 52개 기관 중 ≥ 45개 성공
- [ ] `sitemap.xml`에 식당 1,000+ URL
- [ ] `/llms.txt` 정상 생성
- [ ] 폐업 신고 폼 동작 (테스트 데이터로)

## Phase 3: 배포·QA·법무 문서 (약 60분)

**목표**: 실제 도메인에서 동작하는 서비스 + 법무 페이지 완비.

### 3.1 법무 페이지
- `/about`, `/privacy`, `/terms`, `/disclaimer`, `/legal` 페이지
- 운영자 신원 실제 값으로 채우기 (운영자 미확정 토큰 다 제거)
- 푸터 최종

### 3.2 API 문서 페이지
- `/api` 페이지 — Swagger UI 임베드 `/openapi.json` 표시

### 3.3 Vercel 배포
- `vercel --prod` 또는 `git push origin main`
- 도메인 연결, DNS 적용
- 환경변수 Production·Preview·Development 모두 설정

### 3.4 GitHub Actions cron 활성화
- `daily-crawl.yml` 활성화
- Slack/이메일 알림 채널 설정

### 3.5 외부 모니터링
- Sentry 프론트·Vercel API Routes 양쪽 연결
- Plausible 또는 GA4 설치
- Google Search Console 등록 + sitemap.xml 제출

### 3.6 자체 QA
- TEST_PLAN.md 의 시나리오 1~10 실행
- 데이터 정확도 샘플 30건 수동 검증
- 모바일·데스크톱·태블릿 viewport
- 키보드 내비게이션
- 다크모드

### 3.7 출시 후 즉시 모니터링 (첫 48h)
- 에러 로그 (Sentry)
- API 호출 분포 (의도치 않은 폭주 감지)
- 운영자 이메일 (정정·삭제 요청)
- 부정 트래픽 (DDoS·스크래핑 폭주)

### Phase 3 셀프 체크리스트
- [ ] 운영자 미확정 토큰 grep 결과 0건 (모든 플레이스홀더 채워짐)
- [ ] 프로덕션 URL 정상 접속
- [ ] HTTPS, HSTS 적용
- [ ] sitemap.xml, robots.txt, llms.txt 접근 가능
- [ ] OpenAPI 스펙 `/openapi.json` 정상
- [ ] 폐업 신고·정보 삭제 요청 폼 실제 동작
- [ ] 운영자 이메일로 테스트 이메일 도달
- [ ] GitHub Actions cron 다음 실행 예정

## 자율 모드 운영 원칙

- 매 Phase 끝에 체크리스트 검증. 실패 시 다음 Phase 넘어가지 말 것.
- 결정사항 변경은 ADR 새로 작성. 기존 ADR 임의 수정 금지.
- LEGAL_PRIVACY.md 정책 위반 코드 발견 시 즉시 머지 거부.
- 4시간 안에 못 끝내는 부분은 v1.1 GitHub Issue로 escalate.
- 의문이 들면 사용자에게 묻고 멈출 것 (자율 실행 ≠ 추측).

## 에러 시 동작

| 에러 | 행동 |
|---|---|
| Neon 연결 실패 | `DATABASE_URL` / `DATABASE_URL_READONLY` 재확인, Neon scale-to-zero 콜드 스타트 대기(최대 5초), 3회 실패 시 중단 보고 |
| R2 업로드 실패 | `R2_*` 키 + 버킷명 재확인, 일시적 5xx면 지수 백오프 3회, 최종 실패 시 R2 캐시 skip하고 in-memory만 사용 |
| 카카오 API 401/403 | 키·도메인 제한 확인, 사용자 보고 후 중단 |
| 카카오 일 한도 초과 | 다음 사이클로 미루기, GitHub Issue 생성 |
| Anthropic 429 | 지수 백오프, 즉시 다음 프로바이더(OpenAI → Gemini)로 폴백 ([ADR-009](adr/ADR-009-multi-llm-provider-routing.md) 매트릭스). 모든 프로바이더 429면 5분 대기 후 재시도 |
| OpenAI 429 / Gemini 429 | 동일 — 다음 프로바이더로 즉시 폴백 |
| 추출 confidence 평균 < 0.8 | 매트릭스의 다음 행으로 escalate (예: Haiku → Sonnet, Flash → Opus). confidence 평균 < 0.5는 즉시 `extraction_failures` 큐 |
| 일일 예산(`LLM_BUDGET_DAILY_USD`) 초과 | 자동 강등 — 모든 작업을 가장 싼 1차 모델로 1주 운영, 알림 |
| Vercel 배포 실패 | 빌드 로그 분석, 환경변수 재확인. 변경 commit 안 한 채 4번 실패 시 중단 |
| Materialized view refresh 실패 | 다음 사이클로 미루기 + 알림 |

## 비상 정지

자율 에이전트가 다음을 감지하면 **즉시 중단하고 사용자에게 보고**:
- 가처분 송달 통지
- 데이터 row count가 7일 평균의 2배 초과 (적재 폭주 = 어딘가 오류)
- API 호출이 1초당 1000회 초과 (오용 또는 DDoS)
- 운영자 이메일 미설정 상태에서 사용자 폼 접수
- 마스킹 검증 실패 (실명이 DB에 평문 저장됨)
