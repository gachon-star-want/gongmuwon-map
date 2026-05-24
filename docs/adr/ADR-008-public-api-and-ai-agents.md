# ADR-008 — 공개 API와 AI 에이전트 친화 노출

- **Status**: Accepted
- **Date**: 2026-05-23

## Context

LLM 에이전트(Claude·ChatGPT·Perplexity·Gemini)가 웹을 직접 크롤링·인용한다. 정식 API와 LLM 친화 메타데이터가 없으면:
- 에이전트가 SPA HTML을 잘못 파싱해 할루시네이션
- 인프라에 부담을 주는 비효율적 스크래핑
- 인용 출처 정확도 보장 불가

## Decision

다음을 모두 노출:

1. **REST API** (`/api/v1/*`) — Supabase PostgREST 자동 노출 + Vercel rewrite로 깔끔한 경로.
2. **OpenAPI 3.1** (`/openapi.json`) — Edge Function이 스키마에서 자동 생성, 1시간 캐시.
3. **llms.txt 표준** (`/llms.txt`, `/llms-full.txt`) — Anthropic·OpenAI가 미는 LLM 친화 사이트맵.
4. **API 문서 페이지** (`/api`) — Swagger UI 임베드.
5. **MCP Server** — v1.1 옵션.

### Rate Limit
- 익명: 60 req/min (AI 봇), 600 req/min (정상 Referer)
- 인증 키: 무제한 (v1.1)

### CORS
- GET 엔드포인트는 `Access-Control-Allow-Origin: *`
- 캐시: `Cache-Control: public, s-maxage=300, stale-while-revalidate=600`

## Consequences

- 에이전트의 잘못된 인용 최소화 (할루시네이션 방지).
- 봇 트래픽을 API로 유도 → 인프라 비용 통제.
- 향후 인증 키 + 광고·후원 모델 잠금 가능.
- 출처 표시 의무를 응답 헤더·llms.txt에 박을 수 있어 공공누리 1유형 준수↑.

## Risks

- 무제한 익명 한도가 부정 사용으로 폭주 → Vercel WAF + KV 토큰 버킷으로 차단.
- AI 봇이 잘못 캐시 → `Cache-Control` + `stale-while-revalidate`로 제한적 신선도.

## Related

- [PUBLIC_API.md](../PUBLIC_API.md), [LEGAL_PRIVACY.md](../LEGAL_PRIVACY.md)
