# ADR-007 — 배포 전략

- **Status**: Accepted (Secrets & functions/migrations 부분 갱신 → [ADR-010](ADR-010-database-stack-migration.md))
- **Date**: 2026-05-23

> **Note (2026-05-24)**: CI/CD의 Edge Functions·Migrations 단계와 Secrets 목록이 [ADR-010](ADR-010-database-stack-migration.md)에 의해 Neon + R2 + Vercel API Routes 가정으로 갱신되었습니다. 아래 본문에는 갱신된 표현을 반영했으나, 원안의 도메인·롤백·48h 모니터링 결정은 그대로 유효합니다.

## Context

CI/CD·환경변수·도메인·롤백을 어떻게 구성할지.

## Decision

### CI/CD
- **Web (Vite SPA) + API Routes**: GitHub push → Vercel 자동 빌드·배포(프론트와 `/api/*` 핸들러가 한 번에 배포됨). Preview URL per PR.
- **Pipeline (Python)**: GitHub Actions cron `daily-crawl.yml`, 매일 03:00 KST. 수동 트리거(workflow_dispatch) 지원.
- **Server-side Functions**: Vercel API Routes로 프론트와 함께 `vercel deploy`. 별도 함수 배포 명령 없음 ([ADR-010](ADR-010-database-stack-migration.md)).
- **Migrations**: `uv run --project services/pipeline public-officer-pipeline apply-schema` 수동 실행 (RLS 변경 신중). 기존 마이그레이션 파일 경로(`supabase/migrations/`)는 commit 히스토리 보존을 위해 유지 — Neon은 경로에 무관.

### 환경
- **Production**: 메인 도메인 + Neon Prod 프로젝트 + Cloudflare R2 prod 버킷.
- **Preview**: Vercel preview URL + Neon **branch** preview DB(PR별 격리, 자동) + R2 prod 버킷 공유.
- **Local**: 로컬 Postgres(`docker run postgres:16`) 또는 Neon 개발 브랜치 + R2 prod 또는 MinIO 로컬.

### Secrets
- `DATABASE_URL` (Neon, service 쓰기), `DATABASE_URL_READONLY` (Neon anon RLS-restricted)
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET=officer-map-raw`
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`
- `KAKAO_REST_KEY` (Vercel API Route 서버 측 전용), `RESEND_API_KEY`
- GitHub Secret (Pipeline + Workflow) + Vercel 환경변수(API Routes)
- Vercel 환경변수 중 `VITE_*` 프리픽스만 클라이언트 노출 (예: `VITE_KAKAO_JS_KEY`)

### 도메인 (이중 운영)

| 도메인 | 역할 | 비고 |
|---|---|---|
| `xn--ob0bo0wl1ax52a.com` (영문, 예 `gongmuwon-map.com`) | **Canonical** | SEO 인덱싱, 메일(`admin@`), API base URL, `/openapi.json`·`/llms.txt`의 절대 URL, JSON-LD `Restaurant.url` |
| `(없음)` (한국어 punycode, 예 `xn--v69ak0xskm.com` = `공무원맵.com`) | **사용자 입구** | 카카오톡·구두 공유 친화. 도착 즉시 영문 도메인으로 **301 redirect**. |

- Vercel 프로젝트 설정에서 두 도메인 모두 연결 + 영문을 **Primary Domain**으로 지정 → 나머지 자동 301.
- DNS: Vercel 또는 Cloudflare(옵션).
- HTTPS·HSTS 자동 적용.
- IDN 이메일 호환성 이슈 회피 위해 **메일은 영문 도메인 전용**.

도메인 1개로 충분하다고 판단되면 영문 도메인 하나만 운영해도 됨 — alias는 선택 사항.

### 롤백
- Vercel: 이전 배포 클릭 한 번으로 promote (프론트 + API Routes 동시 롤백).
- Neon migration: `pg_dump` 백업본으로 reverse migration 수동 작성 + Neon Point-in-Time Restore 브랜치 활용.
- 데이터 롤백: Neon Point-in-Time Restore (Free 24시간 / Launch 7일+) 또는 GitHub Actions 주간 `pg_dump` 백업본.

### 첫 출시 후 48h 모니터링
- Sentry, Vercel logs(프론트 + API Routes), Neon logs 매시간 체크.
- 운영자 이메일 응답 SLA 1시간 목표.

## Consequences

- git push만으로 프론트 + API Routes 동시 배포 → 자율 모드 친화.
- Migration은 자동화하지 않음 → 사람 검토 게이트(`psql` 수동 적용).
- Preview URL + Neon 브랜치 preview DB로 PR마다 격리 검증 가능.

## Related

- [RUNBOOK.md](../RUNBOOK.md), [TEST_PLAN.md](../TEST_PLAN.md), [ADR-010](ADR-010-database-stack-migration.md)
