# ADR-010 — 데이터 스택 마이그레이션 (Supabase → Neon + R2 + Vercel)

- **Status**: Accepted
- **Date**: 2026-05-24
- **Supersedes (부분)**: [ADR-006](ADR-006-stack.md) (Supabase 부분만), [ADR-007](ADR-007-deployment-strategy.md) (배포 secrets 부분만)

## Context

- [ADR-006](ADR-006-stack.md)에서 Supabase를 선택했으나, 운영자(wylee0806@naver.com) Supabase 무료 플랜의 활성 프로젝트 2/2 슬롯이 다른 프로젝트(`dental-fit-db`, `crownops-dentalsync`)로 이미 점유됨.
- 기존 프로젝트를 pause/delete 하지 않기로 결정. 유료 업그레이드 비용도 v1에선 회피.
- 동시에 운영자가 Cloudflare + Neon 계정을 이미 보유 + CLI 인증 완료(2026-05-24 확인).
- Vercel 프로젝트·GitHub 저장소·도메인은 Supabase 가정 하에 이미 설정되어 있으며, 본 ADR 적용 시에도 그대로 유지(파괴적 변경 없음).

## Decision

| 영역 | OLD (Supabase) | NEW |
|---|---|---|
| DB | Supabase Postgres | **Neon Postgres** (serverless, scale-to-zero, branching) |
| Object Storage | Supabase Storage | **Cloudflare R2** (S3-compatible, egress free, 10GB free) |
| Server-side Functions | Supabase Edge Functions (Deno) | **Vercel API Routes** (Node.js/TypeScript, 프론트와 동일 Vercel 프로젝트) |
| 인증 | Supabase Auth | v1엔 사용 안 함 (anon-only). **v1.1 — Clerk 무료 플랜 후보** |
| 행 단위 권한 | Supabase RLS | **Postgres RLS** (RLS는 Postgres 표준 기능, Neon에서 동일 SQL 동작) |
| 공개 REST API | PostgREST 자동 노출 | **Vercel API Routes — v1엔 손으로 작성한 엔드포인트.** v1.1 옵션: Render에 PostgREST 셀프호스트 |
| `SUPABASE_URL` | — | `DATABASE_URL` (Neon 연결 문자열, service 쓰기용) |
| `SUPABASE_ANON_KEY` | — | `DATABASE_URL_READONLY` (Neon RLS-restricted 역할 연결 문자열) |
| `SUPABASE_SERVICE_ROLE_KEY` | — | `DATABASE_URL` (위와 동일) |
| 스토리지 경로 | `supabase://...` | `r2://officer-map-raw/...` |
| 마이그레이션 적용 | `supabase db push` | `uv run --project services/pipeline public-officer-pipeline apply-schema` (파일 경로는 유지) |
| Functions 배포 | `supabase functions deploy` | `vercel deploy` (프론트와 함께 배포) |
| 로컬 개발 | `supabase start` (Docker) | `docker run postgres:16` + 익스텐션, 또는 Neon 브랜치 preview |

## Rationale

- **Neon**: PostGIS 호환 표준 Postgres, scale-to-zero(쿼리 없을 때 0원), branch별 격리된 preview DB, 0.5GB 무료. 마이그레이션 SQL이 표준 Postgres만 사용하므로 그대로 portable.
- **Cloudflare R2**: egress 무료 — LLM API에 raw 파일(PDF/HWP/XLSX) 전달할 때 Supabase Storage 대비 트래픽 비용 0. S3 호환이라 SDK 친화.
- **Vercel API Routes**: 프론트와 동일 프로젝트에 함수 동거 → 별도 Edge Function 콘솔/배포 파이프라인 없음. Hobby 플랜 함수 실행 무제한(timeout 10s 제한은 cron으로 회피).

## Consequences

- 마이그레이션 SQL 파일(`supabase/migrations/20260523235106_initial.sql`)은 그대로 portable. `auth.uid()` 같은 Supabase 전용 함수 미사용, 표준 Postgres 기능만 사용. 파일 경로는 GitHub commit 히스토리 보존을 위해 유지(파일명에 "supabase"가 들어가지만 Neon은 경로에 무관).
- Neon에 `anon` / `authenticated` / `service_role` 역할이 기본 제공되지 않음 → 마이그레이션 상단 bootstrap 블록이 NOLOGIN 역할을 idempotent하게 생성.
- PostgREST 자동 REST 노출 사라짐 → Vercel API Routes에 v1 엔드포인트 4~5개 수동 작성. v1.1에서 Render에 PostgREST 셀프호스트 검토.
- Realtime / Supabase Auth / Supabase Storage 콘솔 사라짐 → v1엔 미사용이라 영향 없음.
- Supabase 로컬 Docker 스택(`supabase start`) → 로컬 Postgres(`docker run postgres:16`) + Neon 브랜치 preview로 대체.
- Edge Function HTTP 핸들러 경로 매핑:
  - `/functions/v1/notice-takedown` → `/api/takedown-request`
  - `/functions/v1/closure-report` → `/api/closure-report`
  - `recompute-grades` → Vercel cron route `/api/cron/recompute-grades`
  - `sitemap-generate` → `/api/sitemap`

## Migration Plan (codex 이어서 실행할 단계)

1. R2 활성화 (Cloudflare 대시보드 1회 클릭, API 토큰 발급).
2. `neonctl projects create gongmuwon-map --org-id <org>` → `DATABASE_URL` 획득.
3. 읽기 전용 Neon 로그인 역할 `app_readonly`를 생성하고 `DATABASE_URL_READONLY`로 사용.
4. `uv run --project services/pipeline public-officer-pipeline apply-schema` (기존 마이그레이션 그대로 적용 — 파일 경로 유지).
5. 파이프라인 코드(`services/pipeline/`)의 `SUPABASE_URL` / `SUPABASE_*_KEY`를 `DATABASE_URL`로 교체.
6. Vercel API Routes 작성:
   - `GET /api/v1/places`
   - `GET /api/v1/places/[id]`
   - `GET /api/v1/places/[id]/visits`
   - `GET /api/v1/agencies`
   - `GET /api/v1/agencies/[id]`
   - `POST /api/closure-report`
   - `POST /api/takedown-request`
   - 추가 cron: `/api/cron/recompute-grades`, `/api/sitemap`
7. R2 버킷 `officer-map-raw` 생성, `sources.storage_path` 포맷을 `r2://officer-map-raw/{agency}/{yyyy-mm}/{hash}.{ext}`로 변경.
8. `.env` 갱신: `SUPABASE_*` 제거, `DATABASE_URL` + `DATABASE_URL_READONLY` + `R2_ACCOUNT_ID` + `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` + `R2_BUCKET` + `RESEND_API_KEY` 추가.
9. GitHub Actions cron(`daily-crawl.yml`)의 secrets 갱신: Supabase 키 제거 + Neon/R2 키 추가.

## Related

- [ADR-006](ADR-006-stack.md) — stack (Supabase 부분 superseded 마킹)
- [ADR-007](ADR-007-deployment-strategy.md) — deployment (secrets 부분 갱신)
- [ADR-008](ADR-008-public-api-and-ai-agents.md) — 공개 API (PostgREST 가정에서 Vercel API Routes 가정으로 갱신)
- [RUNBOOK.md](../RUNBOOK.md) — Phase 1 setup 명령 재실행
- [TECH_STACK.md](../TECH_STACK.md) — 비용·도구 표 갱신
