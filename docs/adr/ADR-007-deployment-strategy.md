# ADR-007 — 배포 전략

- **Status**: Accepted
- **Date**: 2026-05-23

## Context

CI/CD·환경변수·도메인·롤백을 어떻게 구성할지.

## Decision

### CI/CD
- **Web (Vite SPA)**: GitHub push → Vercel 자동 빌드·배포. Preview URL per PR.
- **Pipeline (Python)**: GitHub Actions cron `daily-crawl.yml`, 매일 03:00 KST. 수동 트리거(workflow_dispatch) 지원.
- **Edge Functions**: `supabase functions deploy` 수동(또는 `.github/workflows/edge-deploy.yml`로 자동화).
- **Migrations**: `supabase db push` 수동 (RLS 변경 신중).

### 환경
- **Production**: 메인 도메인 + Supabase Prod 프로젝트.
- **Preview**: Vercel preview URL + Supabase Staging 프로젝트(공유 비용 절감 시 Prod RLS 의존).
- **Local**: `supabase start` 로컬 Docker.

### Secrets
- `ANTHROPIC_API_KEY`, `KAKAO_REST_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`
- GitHub Secret (Pipeline) + Supabase Edge Function Secret(Edge)
- Vercel 환경변수는 `VITE_*` 프리픽스만 클라이언트 노출

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
- Vercel: 이전 배포 클릭 한 번으로 promote.
- Supabase migration: `supabase db pull` 후 reverse migration 수동 작성.
- 데이터 롤백: `pg_restore` (Pro plan 자동 백업 활용).

### 첫 출시 후 48h 모니터링
- Sentry, Vercel logs, Supabase logs 매시간 체크.
- 운영자 이메일 응답 SLA 1시간 목표.

## Consequences

- git push만으로 프론트 배포 → 자율 모드 친화.
- Edge Function·migration은 자동화하지 않음 → 사람 검토 게이트.
- Preview URL로 PR마다 검증 가능.

## Related

- [RUNBOOK.md](../RUNBOOK.md), [TEST_PLAN.md](../TEST_PLAN.md)
