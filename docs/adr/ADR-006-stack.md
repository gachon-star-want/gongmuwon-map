# ADR-006 — 풀스택 조합: Vite + React + Mantine + Supabase + Vercel

- **Status**: Accepted
- **Date**: 2026-05-23

## Context

자율 모드 안정성·개발 속도·LLM 생성 친화도가 결정 기준.

## Decision

| 영역 | 선택 |
|---|---|
| Frontend Build | **Vite** |
| Framework | **React + TypeScript** |
| UI | **Mantine** |
| 상태 | **TanStack Query + Zustand** |
| Backend | **Supabase (Postgres + RLS + Edge Functions + Storage + Auth)** |
| Map | **카카오맵** |
| 호스팅 | **Vercel** |
| Crawler | **Python 3.12 on GitHub Actions** |
| LLM | **Anthropic Claude (Haiku/Sonnet 라우팅)** |

## Consequences

- 거지맵·kofficer-guide 동일 조합 → 검증된 패턴, LLM 생성 코드 정확도 최상.
- Supabase 단일 의존으로 인프라 복잡도↓.
- Vite SPA로 자율 에이전트가 SSR 경계 헛디딤 회피.
- PostgREST 자동 REST 노출로 [ADR-008](ADR-008-public-api-and-ai-agents.md) 공개 API 구현 비용↓.

## Alternatives Considered

- Next.js App Router: SSR·SEO 좋지만 자율 에이전트 안정성↓.
- Cloudflare Pages: Supabase와 거리 멀어 운영 복잡.
- Firebase: NoSQL이라 식당-방문-기관 관계 모델 약함.
- 자체 Postgres + Express: 4시간 안에 무리.

## Related

- [TECH_STACK.md](../TECH_STACK.md)
