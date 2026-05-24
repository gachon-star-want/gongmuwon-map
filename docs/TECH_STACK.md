# TECH_STACK — 도구 선정 + 근거

각 선택의 **이유**가 핵심. 대체안과 트레이드오프도 명시.

## 한눈에 보는 표

| 영역 | 선택 | 대안 | 근거 |
|---|---|---|---|
| 프론트 빌드 | **Vite** | Next.js | SPA 충분 + 빌드 빠름 + Vercel 친화 |
| 프론트 프레임워크 | **React + TypeScript** | Vue, Svelte | LLM 생성 정확도 + 생태계 |
| UI 라이브러리 | **Mantine** | shadcn/ui, Chakra | 다이얼로그·드로어·테이블·폼 다 내장, 거지맵·다수 한국 SPA가 채택 |
| 상태 관리 | **TanStack Query + Zustand** | Redux | 서버 캐시·낙관적 업데이트 + 가벼운 UI 상태 |
| 지도 | **카카오맵 JS API** | 네이버맵, Mapbox, Leaflet | 카카오 로컬 placeId와 entity resolution 정합 |
| 지오코딩 | **카카오 로컬 API** | 네이버 Geocoding, VWorld | 식당 검색 정확도·한국 도로명 처리 우수 |
| DB | **Neon Postgres** (serverless, branching) | Supabase, RDS, 자체 Postgres | scale-to-zero + PR별 브랜치 preview + RLS 표준 Postgres 그대로 ([ADR-010](adr/ADR-010-database-stack-migration.md)) |
| Object Storage | **Cloudflare R2** | Supabase Storage, S3 | egress 무료 → LLM에 raw 파일 전달 시 비용 0, 10GB 무료 ([ADR-010](adr/ADR-010-database-stack-migration.md)) |
| Server-side Functions | **Vercel API Routes (Node.js/TS)** | Supabase Edge Functions, Cloudflare Workers | 프론트와 동일 Vercel 프로젝트, Hobby 함수 실행 무제한 |
| 인증 | **(v1엔 없음, anon-only)** | Supabase Auth, Clerk | v1.1 — Clerk 무료 플랜 후보 |
| 호스팅 (프론트) | **Vercel** | Cloudflare Pages, Netlify | git push 즉시 배포 + Preview URL + CDN |
| LLM | **Anthropic + OpenAI + Gemini (멀티 프로바이더)** | 단일 의존 | 장애 대응 + 비용 최적화 + 모델별 강점 활용 ([ADR-009](adr/ADR-009-multi-llm-provider-routing.md)) |
| 크롤러 실행 | **GitHub Actions cron** | Render Cron, Vercel Cron | 무료 한도 충분, 빌드/배포와 한 곳 관리 |
| 크롤러 언어 | **Python 3.12** | Node.js | pdfplumber·openpyxl·pyhwp가 Python에 모임 |
| HTTP 클라이언트 | **httpx** (Python) | requests | async + HTTP/2 + 타임아웃 표준 |
| 동적 렌더링 폴백 | **Playwright (Chromium)** | Selenium | 한국 정부 사이트가 JS 렌더링 요구하는 경우 |
| 파일 파서 | **pdfplumber / openpyxl / pyhwp** | PyPDF2, libhwp | 표 추출 정확도 + 한글 인코딩 안정 |
| OCR 폴백 | **Claude Opus 4.7 vision** (해상도 3x 점프) | Tesseract, Sonnet vision | 스캔 PDF·한국어 표 OCR 정확도 결정타. 그냥 LLM에 이미지 던지면 됨 ([ADR-009](adr/ADR-009-multi-llm-provider-routing.md)) |
| 이메일 알림 | **Resend** | SES, Mailgun | 운영자 1인 워크플로 단순 |
| 에러 트래킹 | **Sentry** | Datadog | 무료 한도, SDK 채택률 |
| 분석 | **Plausible** | GA4 | privacy-friendly (한국 개인정보보호위 정렬), 다만 비용 → v1.1엔 GA4도 검토 |

## 선택 근거 상세

### Vite + React + Mantine
- 거지맵(`vue-router` 아님), cham-monimap, kofficer-guide **세 선례 모두 Vite + React + 카카오맵**.
- LLM 생성 코드 정확도가 가장 높은 조합 (자율 모드 친화).
- Mantine는 한국 SaaS에서 채택률 높음 + 다국어(i18n) + 다크모드 내장.

### Neon + Cloudflare R2 + Vercel API Routes 조합 ([ADR-010](adr/ADR-010-database-stack-migration.md))
- **Neon Postgres**: scale-to-zero(쿼리 없을 때 0원) + branch별 격리된 preview DB + PostGIS·earthdistance 같은 표준 확장 지원. RLS는 Postgres 표준 기능이라 마이그레이션 SQL이 그대로 portable.
- **Cloudflare R2**: egress 무료라 LLM에 raw PDF/HWP/XLSX 전달 시 트래픽 비용 0. S3 호환이라 boto3·AWS SDK 그대로.
- **Vercel API Routes**: 프론트와 동일 프로젝트에서 함수 동거. 별도 콘솔/배포 파이프라인 없음. Hobby 플랜 함수 실행 무제한(timeout 10s, cron으로 회피 가능).
- **RLS로 anon 권한 잠그고, 공개는 `*_public` 뷰로만** — 거지맵의 검증된 보안 패턴(Postgres 표준이라 Neon에서도 동일).
- 공개 REST는 PostgREST 자동 노출이 사라지므로 v1엔 API Route 4~5개 수기 작성. v1.1에서 Render에 PostgREST 셀프호스트 검토.
- 이전(Supabase 단일 의존) 가정은 [ADR-006](adr/ADR-006-stack.md) 참조.

### Vercel
- GitHub push → 자동 빌드·배포 + Preview URL.
- 가처분 송달 우려 시 미국 회사 호스팅 = 사실상 표현의 자유 보호막.
- Edge Network로 한국 사용자 응답 < 100ms.

### LLM 멀티 프로바이더 (Anthropic + OpenAI + Gemini)
- **장애 대응**: 한 프로바이더 5xx/429면 즉시 다음 프로바이더로.
- **비용 최적화**: 작업 유형별 가장 싸고 정확한 모델 선택. 일일 예산 가드레일.
- **모델별 강점** (2026-05-24 기준):
  - **Gemini 3.5 Flash** (2026-05-19 출시, $1.50/$9 per M): 한국어 표 대량 추출 1차 워크호스, Gemini 3.1 Pro급 성능을 4x 빠르게
  - **Claude Opus 4.7** (2026-04 출시, $5/$25): PDF 비전 1차 — vision 해상도 3x 점프(2,576px / 3.75MP)로 스캔 PDF 결정타
  - **Claude Sonnet 4.6** (2026-02 출시, $3/$15): 마스킹 검증·식당명 정규화 같이 정확도 critical 케이스
  - **Claude Haiku 4.5** (2025-10 출시, $1/$5): PDF 표·구조화 데이터 신뢰도 + 저비용
  - **GPT-5.5** (2026-04-24 출시): 폴백 다양성 + `reasoning.effort` 가변
- **Thinking/Reasoning budget 명시 라우팅**: 작업별로 Anthropic `extended_thinking.budget_tokens` / OpenAI `reasoning.effort` / Gemini `thinking_level` 하드코딩 (대량 처리는 minimal·off, 마스킹 검증은 16K·high).
- **통일 인터페이스**: `LLMClient.extract(task, prompt, schema)` — 호출자는 어느 프로바이더가 응답하는지 몰라도 됨.
- 상세는 [ADR-009](adr/ADR-009-multi-llm-provider-routing.md).

### GitHub Actions cron
- 매일 03:00 KST 1회 실행, 평균 20분 소요 추정 → 월 약 600분 < 무료 2,000분.
- Secret으로 Anthropic API 키·`DATABASE_URL`(Neon)·`R2_*` 키·Kakao REST 키 보관.
- 실패 시 GitHub Issue 자동 생성.

## 폴더 구조 (예상)

```
/
├─ AGENTS.md                       # 모든 AI 에이전트 부팅 파일 (Codex·Claude Code 공통)
├─ docs/
├─ apps/
│  └─ web/                        # Vite SPA
│     ├─ src/
│     ├─ public/
│     │  ├─ llms.txt
│     │  ├─ llms-full.txt
│     │  └─ openapi.json
│     ├─ vite.config.ts
│     └─ package.json
├─ services/
│  └─ pipeline/                   # Python 크롤러
│     ├─ crawler/
│     ├─ extractor/
│     ├─ normalizer/
│     ├─ entity/
│     ├─ loader/
│     ├─ pyproject.toml
│     └─ Dockerfile
├─ api/                           # Vercel API Routes (Node.js/TypeScript)
│  ├─ places/
│  │  ├─ places.ts                # GET /api/v1/places
│  │  └─ places/[id].ts           # GET /api/v1/places/[id]
│  ├─ takedown-request.ts         # POST /api/takedown-request
│  ├─ closure-report.ts           # POST /api/closure-report
│  ├─ sitemap.ts                  # GET /api/sitemap
│  └─ cron/
│     └─ recompute-grades.ts      # Vercel Cron
├─ supabase/
│  ├─ migrations/                 # SQL 마이그레이션 (Neon에 apply-schema로 적용, 파일 경로는 commit 히스토리 보존을 위해 유지)
│  └─ seed.sql
├─ .github/
│  └─ workflows/
│     ├─ daily-crawl.yml
│     ├─ web-deploy.yml
│     └─ pipeline-test.yml
└─ package.json                   # workspace root (옵션)
```

## 비용 예상 (월간)

| 항목 | 예상 |
|---|---|
| Neon (Free → Launch $19/월) | $0 (v1, 0.5GB 한도 내) |
| Cloudflare R2 | $0 (10GB · egress 무료) |
| Vercel Hobby (당분간) | $0 (함수 실행 무제한) |
| LLM API (Anthropic + OpenAI + Gemini 합산) | $30~100 (라우팅·예산 가드레일에 따라) |
| 카카오 로컬·지도 API | $0 (무료 한도 내) |
| GitHub Actions | $0 (무료 한도 내) |
| Resend | $0 (무료 100건) |
| 도메인 | ~$15/년 |
| **합계** | **~$30~110/월** |

광고 미적용 시 운영자 자비. v1.1에 AdSense 검토. Supabase 가정 대비 인프라 고정비 $25 절감(자세한 사유 [ADR-010](adr/ADR-010-database-stack-migration.md)).

## 미적용한 옵션 (의도적 배제)

- **Next.js App Router**: SSR 좋지만 자율 에이전트가 Server Component 경계에서 자주 발 헛디딤. Vite SPA가 더 안정적.
- **Cloudflare Workers**: Edge 컴퓨팅 빠르지만 Vercel API Routes와 분리되어 운영 복잡. (R2는 별도로 활용)
- **Supabase 단일 의존(원안)**: [ADR-010](adr/ADR-010-database-stack-migration.md) 사유로 v1엔 회피.
- **자체 Postgres + 인증**: Neon serverless가 v1 부담 줄여줌.
- **MongoDB**: 식당-방문-기관-부서 관계가 강해서 RDBMS가 우수.
