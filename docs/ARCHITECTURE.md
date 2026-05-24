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
│   (httpx/    (pdfplumber/      (PDF→txt,           (Anthropic API,      │
│    Playwright) openpyxl/        OCR fallback)       Haiku/Sonnet 라우팅) │
│    pyhwp)                                                              │
│                                                                         │
│   ↓ 정규화된 JSON (trip, restaurant_raw)                                │
│                                                                         │
│   Entity Resolver  →  Geocoder  →  Upsert Worker                        │
│   (카카오 로컬 API)   (placeId 기반   (Supabase REST)                    │
│                       좌표/주소 확정)                                    │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Supabase (Postgres + RLS + Auth)                      │
│                                                                         │
│   places   place_visits   agencies   place_closure_reports              │
│   places_public(VIEW)   agency_stats(VIEW)   place_grade_v1(MAT VIEW)   │
│                                                                         │
│   Edge Functions (HTTP API, Deno):                                       │
│     - notice-takedown   → RPC request_takedown 호출 + 운영자 이메일      │
│     - closure-report    → RPC report_closure 호출                       │
│     - recompute-grades  → REFRESH MAT VIEW (매일 새벽)                  │
│     - sitemap-generate  → sitemap.xml + llms.txt 정적 생성              │
│                                                                         │
│   Postgres RPC (anon 쓰기 진입점):                                       │
│     - request_takedown(place_id, reason, email)                         │
│     - report_closure(place_id, fp, note)                                │
│     - mark_reopen(place_id, fp)                                         │
│                                                                         │
│   Storage:                                                              │
│     - raw-sources/      (원본 PDF/HTML 캐시, 30일 TTL)                  │
└──────────┬──────────────────────────────────┬───────────────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐         ┌──────────────────────────────────┐
│ 사용자용 Web (SPA)   │         │ 공개 API (PostgREST 자동)        │
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
  - `loader/` — Supabase REST upsert

상세: [PIPELINE.md](PIPELINE.md)

### 2. Datastore
- **Supabase**: Postgres + RLS + Auth + Edge Functions + Storage
- **읽기 정책**: `*_public` 뷰만 anon role 노출, 원본 테이블은 service role 전용
- **쓰기 정책**: 모든 사용자 쓰기는 RPC 함수를 통해서만 (거지맵 패턴)

상세: [DATA_MODEL.md](DATA_MODEL.md)

### 3. Frontend (SPA)
- **Vite + React + TypeScript + Mantine**
- **지도**: 카카오맵 JS API + 마커 클러스터링
- **상태 관리**: TanStack Query(API 캐시) + Zustand(UI 상태)
- **라우팅**: react-router (`/`, `/r/:slug`, `/agency/:id`, `/about`, `/privacy`, `/terms`)
- **SEO**: SPA지만 path별 메타태그 JS 주입 + Edge Function이 생성하는 정적 sitemap.xml

상세: [UI_UX.md](UI_UX.md), [TECH_STACK.md](TECH_STACK.md)

### 4. Public API
- **REST**: Supabase PostgREST 자동 노출 + `/rest/v1/places_public` 등을 `/api/v1/places`로 리버스 프록시
- **OpenAPI 3.1**: Edge Function이 스키마에서 자동 생성
- **llms.txt 표준**: 루트에 `/llms.txt`, `/llms-full.txt`
- **MCP server**: v1.1 옵션

상세: [PUBLIC_API.md](PUBLIC_API.md)

## 데이터 흐름

### 일일 갱신 흐름
1. GitHub Actions 매일 03:00 KST 트리거
2. 52개 소스 × 최근 30일치 게시 목록 페치
3. 신규 또는 갱신된 게시물의 첨부 파일 다운로드 (Supabase Storage 캐시)
4. PDF/HWP/XLSX → 텍스트 추출
5. LLM에 텍스트 + 기관 메타데이터 전달 → 정규화 JSON 출력
6. 식당 entity resolution (카카오 로컬 API)
7. `place_visits` 테이블 upsert (자연키: `agency_id + visit_date + place_id + amount`)
8. `recompute-grades` Edge Function 실행 → `place_grade_v1` 갱신
9. `sitemap-generate` Edge Function 실행 → 정적 파일 갱신

### 사용자 조회 흐름
1. 사용자 브라우저 → SPA 로드
2. SPA → 카카오맵 SDK 초기화
3. SPA → Supabase REST `places_public?bbox=...&grade=in.(★★★,★★)` 호출
4. 마커 렌더링 (클러스터링 적용)
5. 마커 클릭 → 디테일 패널 → `places_public/{id}` + `place_visits_by_place(id)` 호출

### AI 에이전트 조회 흐름
1. 에이전트 → `/llms.txt` 읽음 → 사이트 구조 파악
2. 에이전트 → `/openapi.json` 페치 → API 사용법 학습
3. 에이전트 → `/api/v1/places?...` 호출 (rate limit 60/min 익명)
4. 응답 캐싱 헤더에 따라 CDN 캐시 활용

## 외부 의존성

| 서비스 | 용도 | 무료 한도 | 폴백 |
|---|---|---|---|
| Supabase | DB·Auth·Functions·Storage | 500MB DB, 1GB Storage, 2GB egress/월 | Pro $25/월 |
| Vercel | 프론트 호스팅·CDN | Hobby plan 충분 | Cloudflare Pages |
| Anthropic API | LLM 정규화 | 종량제 | OpenAI / 자체 추출기 |
| 카카오 로컬 API | placeId·지오코딩 | 일 30,000회 | 네이버 로컬 |
| 카카오맵 JS API | 지도 렌더링 | 일 300,000회 | 네이버맵 |
| GitHub Actions | 배치 실행 | 월 2,000분 | self-hosted runner |
| Resend / SES | 운영자 이메일 알림 | 월 100건 | Sendgrid |

## 보안

- **API 키 누설 방지**: 카카오 REST API 키는 Edge Function 안에서만 사용. JS 키는 도메인 제한.
- **RLS**: 원본 테이블은 anon 차단. 공개는 view로만.
- **Rate limit**: Vercel WAF + Supabase Edge Function 토큰 버킷.
- **CSP**: `default-src 'self'` + 카카오·Vercel·Supabase·GA 도메인 화이트리스트.

## 관측성

- **로깅**: Supabase logs + Vercel logs (자동)
- **에러 트래킹**: Sentry (프론트·Edge Function 양쪽)
- **분석**: Plausible (privacy-friendly) 또는 GA4
- **데이터 품질 알림**: 매일 추출 결과 row 수가 7일 평균 대비 ±30% 벗어나면 Slack/이메일
