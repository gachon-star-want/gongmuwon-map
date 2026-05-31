# ARCHITECTURE — 공무원맵 시스템 구조

## 한눈에 보는 그림

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          외부 데이터 소스                                │
│   서울 정보소통광장(HTML)   자치구·의회 게시판(PDF/HWP/XLSX)             │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │  (GitHub Actions, 매일 1회 cron)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           Pipeline (Python on GitHub Actions Runner)                     │
│                                                                         │
│   Crawler  →  Fetcher(파일)  →  Text Extractor  →  LLM Normalizer       │
│   (httpx/    (pdfplumber/      (PDF→txt,           (멀티 프로바이더      │
│    Playwright) openpyxl/        OCR fallback)       라우팅 — ADR-009)   │
│    pyhwp)                                                              │
│                                                                         │
│   ↓ 정규화된 JSON (trip, restaurant_raw)                                │
│                                                                         │
│   Entity Resolver  →  Geocoder  →  Upsert Worker                        │
│   (카카오 로컬 API)   (placeId 기반   (Neon Postgres,                    │
│                       좌표/주소 확정)  node-postgres / drizzle)          │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Neon (Serverless Postgres + RLS) + Cloudflare R2            │
│                                                                         │
│   places   place_visits   agencies   place_closure_reports              │
│   places_public(VIEW)   agency_stats(VIEW)   place_grade_v1(MAT VIEW)   │
│                                                                         │
│   Vercel API Routes (Node.js/TypeScript, 프론트와 동일 프로젝트):         │
│     - POST /api/takedown-request   → request_takedown SQL + 운영자 메일  │
│     - POST /api/closure-report     → report_closure SQL 호출            │
│     - GET  /api/cron/recompute-grades → REFRESH MAT VIEW (Vercel Cron)  │
│     - GET  /api/sitemap            → sitemap.xml + llms.txt 동적 응답   │
│     - GET  /api/places, /api/places/[id], /api/agencies(+ /[id])        │
│                                                                         │
│   Postgres SQL 함수 (service role 호출, anon 쓰기 진입점은 API Routes): │
│     - request_takedown(place_id, reason, email)                         │
│     - report_closure(place_id, fp, note)                                │
│     - mark_reopen(place_id, fp)                                         │
│                                                                         │
│   Object Storage (Cloudflare R2):                                       │
│     - r2://officer-map-raw/   (원본 PDF/HTML 캐시, 30일 TTL, egress 무료) │
└──────────┬──────────────────────────────────┬───────────────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐         ┌──────────────────────────────────┐
│ 사용자용 Web (SPA)   │         │ 공개 API (Vercel API Routes)      │
│ Vercel + Vite + React│         │ /api/v1/* + /openapi.json        │
│ + Mantine + 카카오맵 │         │ + /llms.txt + /llms-full.txt     │
└──────────┬───────────┘         └────────────┬─────────────────────┘
           │                                  │
           ▼                                  ▼
   일반 사용자(브라우저)             AI 에이전트(Claude·ChatGPT·Perplexity)
                                     서드파티 개발자
```

## 컴포넌트 계층

### 1. Pipeline (배치)
- **실행 환경**: GitHub Actions Runner (Ubuntu), 매일 03:00 KST
- **언어**: Python 3.12
- **모듈**:
  - `crawler/` — 사이트별 어댑터 (옅은 패턴, 대부분 LLM에 위임)
  - `extractor/` — 파일 → 텍스트 변환(pdfplumber/openpyxl/pyhwp + OCR 폴백)
  - `normalizer/` — Anthropic SDK 호출, 정규화 JSON 스키마
  - `entity/` — 카카오 로컬 API 매칭 + 폴백
  - `loader/` — Neon Postgres upsert (psycopg / asyncpg)

상세: [PIPELINE.md](PIPELINE.md)

### 2. Datastore
- **Neon Postgres**: serverless Postgres + RLS + scale-to-zero + branching ([ADR-010](adr/ADR-010-database-stack-migration.md))
- **Cloudflare R2**: 원본 파일(PDF/HWP/XLSX) object storage, S3 호환, egress 무료
- **읽기 정책**: `*_public` 뷰만 `anon` role 노출, 원본 테이블은 `service_role` 전용 (RLS는 Postgres 표준 기능)
- **쓰기 정책**: 모든 사용자 쓰기는 Vercel API Routes를 거쳐 SQL 함수 호출 (거지맵 패턴 + Supabase 시절 RPC 함수를 API Route 핸들러가 감쌈)
- **인증**: v1엔 없음(anon-only). v1.1에서 Clerk 무료 플랜 후보.

상세: [DATA_MODEL.md](DATA_MODEL.md)

### 3. Frontend (SPA)
- **Vite + React + TypeScript + Mantine**
- **지도**: 카카오맵 JS API + 마커 클러스터링
- **상태 관리**: TanStack Query(API 캐시) + Zustand(UI 상태)
- **라우팅**: react-router (`/`, `/r/:slug`, `/agency/:id`, `/about`, `/privacy`, `/terms`)
- **SEO**: SPA지만 path별 메타태그 JS 주입 + Vercel API Route(`/api/sitemap`)가 동적으로 응답하는 sitemap.xml (Vercel Cron이 정기 워밍)

상세: [UI_UX.md](UI_UX.md), [TECH_STACK.md](TECH_STACK.md)

### 4. Public API
- **REST**: Vercel API Routes에 v1 엔드포인트 5개를 수기 작성(`/api/places`, `/api/places/[id]`, `/api/places/[id]/visits`, `/api/agencies`, `/api/agencies/[id]`). 핸들러가 Neon에 SQL 실행 후 `*_public` 뷰의 JSON을 반환.
- **OpenAPI 3.1**: 정적 `/openapi.json` (빌드 시 생성, 1시간 캐시).
- **llms.txt 표준**: 루트에 `/llms.txt`, `/llms-full.txt`.
- **MCP server**: v1.1 옵션. PostgREST 셀프호스트(Render) 옵션도 v1.1에서 검토.

상세: [PUBLIC_API.md](PUBLIC_API.md)

## 데이터 흐름

### 일일 갱신 흐름
1. GitHub Actions 매일 03:00 KST 트리거
2. 52개 소스 × 최근 30일치 게시 목록 페치
3. 신규 또는 갱신된 게시물의 첨부 파일 다운로드 (Cloudflare R2 `officer-map-raw/` 캐시)
4. PDF/HWP/XLSX → 텍스트 추출
5. LLM에 텍스트 + 기관 메타데이터 전달 → 정규화 JSON 출력
6. 식당 entity resolution (카카오 로컬 API)
7. `place_visits` 테이블 upsert (자연키: `agency_id + visit_date + place_id + amount`)
8. Vercel Cron이 `/api/cron/recompute-grades` 호출 → `place_grade_v1` 갱신
9. Vercel Cron이 `/api/sitemap` 워밍 → 캐시 갱신

### 사용자 조회 흐름
1. 사용자 브라우저 → SPA 로드
2. SPA → 카카오맵 SDK 초기화
3. SPA → Vercel API Route `/api/places?bbox=...&grade=in.(★★★,★★)` 호출 (서버에서 Neon 쿼리)
4. 마커 렌더링 (클러스터링 적용)
5. 마커 클릭 → 디테일 패널 → `/api/places/{id}` + `/api/places/{id}/visits` 호출

### AI 에이전트 조회 흐름
1. 에이전트 → `/llms.txt` 읽음 → 사이트 구조 파악
2. 에이전트 → `/openapi.json` 페치 → API 사용법 학습
3. 에이전트 → `/api/v1/places?...` 호출 (rate limit 60/min 익명)
4. 응답 캐싱 헤더에 따라 CDN 캐시 활용

## 외부 의존성

| 서비스 | 용도 | 무료 한도 | 폴백 |
|---|---|---|---|
| Neon | Postgres DB (serverless, branching) | 0.5GB storage, scale-to-zero | Launch $19/월 |
| Cloudflare R2 | Object Storage (raw 파일 캐시) | 10GB, egress 무료 | Backblaze B2 |
| Vercel | 프론트 호스팅·CDN·API Routes·Cron | Hobby plan 충분 (함수 실행 무제한, 10s timeout) | Cloudflare Pages + Workers |
| Anthropic API | LLM 정규화 | 종량제 | OpenAI / 자체 추출기 |
| 카카오 로컬 API | placeId·지오코딩 | 일 30,000회 | 네이버 로컬 |
| 카카오맵 JS API | 지도 렌더링 | 일 300,000회 | 네이버맵 |
| GitHub Actions | 배치 실행 | 월 2,000분 | self-hosted runner |
| Resend / SES | 운영자 이메일 알림 | 월 100건 | Sendgrid |

## 보안

- **API 키 누설 방지**: 카카오 REST API 키는 Vercel API Route 핸들러 안에서만 사용. JS 키는 도메인 제한.
- **DB 자격 증명 분리**: `DATABASE_URL` (service 쓰기) vs `DATABASE_URL_READONLY` (anon RLS-restricted). API Route는 요청 종류에 맞는 connection string 사용.
- **RLS**: 원본 테이블은 `anon` 차단. 공개는 view로만 (Postgres 표준 RLS, Neon에서 동일).
- **Rate limit**: 현재 고위험 쓰기 API Route에는 인메모리 fixed-window 제한을 적용한다(서버리스 인스턴스별 best-effort). 전역 일관 제한은 이후 WAF/edge 또는 공유 KV·Redis 계층에서 보강한다.
- **CSP**: `default-src 'self'` + 카카오·Vercel·Cloudflare R2·GA 도메인 화이트리스트.

## 관측성

- **로깅**: Vercel logs (프론트 + API Routes 통합) + Neon logs
- **에러 트래킹**: Sentry (프론트·API Routes 양쪽)
- **분석**: Plausible (privacy-friendly) 또는 GA4
- **데이터 품질 알림**: 매일 추출 결과 row 수가 7일 평균 대비 ±30% 벗어나면 Slack/이메일
