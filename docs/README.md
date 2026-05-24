# docs/ — 공무원맵 설계 문서

이 폴더는 **공무원맵의 single source of truth**입니다. 모든 코드는 이 문서에서 파생됩니다.

## 빠른 인덱스

### 무엇·왜 (Product)
- [PRD.md](PRD.md) — 제품 요구사항. 사용자·문제·가치 제안·v1 스코프·성공 지표.
- [CHANGELOG.md](CHANGELOG.md) — v1 / v1.1 / v2 로드맵.

### 어떻게 (Engineering)
- [ARCHITECTURE.md](ARCHITECTURE.md) — 컴포넌트 다이어그램·데이터 흐름.
- [TECH_STACK.md](TECH_STACK.md) — 사용 도구 + 선정 근거.
- [DATA_MODEL.md](DATA_MODEL.md) — Neon Postgres 테이블·뷰·RLS·entity resolution.
- [PIPELINE.md](PIPELINE.md) — 크롤 → 파싱(LLM) → 정규화 → 지오코딩 → 적재.
- [ALGORITHM.md](ALGORITHM.md) — 등급 공식·백분위·시간 윈도우·폐업 처리.
- [UI_UX.md](UI_UX.md) — 지도·마커·필터·디테일 패널 사양.
- [PUBLIC_API.md](PUBLIC_API.md) — REST API·OpenAPI 스펙·llms.txt·MCP server.

### 법·운영 (Compliance & Ops)
- [LEGAL_PRIVACY.md](LEGAL_PRIVACY.md) — 공공누리·정보공개법·표기 정책·면책 조항.
- [RISK_MITIGATION.md](RISK_MITIGATION.md) — 민원 대응·가처분 플레이북·노티스앤테이크다운.

### 실행 (Execution)
- [RUNBOOK.md](RUNBOOK.md) — 자율 모드 3단계 실행 순서.
- [TEST_PLAN.md](TEST_PLAN.md) — 데이터 검증·E2E·수동 QA.

### 박제된 결정 (Architecture Decision Records)
- [adr/ADR-001-data-source-strategy.md](adr/ADR-001-data-source-strategy.md)
- [adr/ADR-002-llm-extraction.md](adr/ADR-002-llm-extraction.md)
- [adr/ADR-003-entity-resolution.md](adr/ADR-003-entity-resolution.md)
- [adr/ADR-004-ranking-formula.md](adr/ADR-004-ranking-formula.md)
- [adr/ADR-005-map-provider.md](adr/ADR-005-map-provider.md)
- [adr/ADR-006-stack.md](adr/ADR-006-stack.md)
- [adr/ADR-007-deployment-strategy.md](adr/ADR-007-deployment-strategy.md)
- [adr/ADR-008-public-api-and-ai-agents.md](adr/ADR-008-public-api-and-ai-agents.md)
- [adr/ADR-009-multi-llm-provider-routing.md](adr/ADR-009-multi-llm-provider-routing.md)
- [adr/ADR-010-database-stack-migration.md](adr/ADR-010-database-stack-migration.md) — Supabase → Neon + R2 + Vercel API Routes 마이그레이션

## 작업 흐름

```
PRD ──┐
      ├─→ ARCHITECTURE ─┬─→ DATA_MODEL ─→ PIPELINE ─→ ALGORITHM
      │                 ├─→ UI_UX
      │                 └─→ PUBLIC_API
      ├─→ TECH_STACK ───→ (각 모듈에 영향)
      └─→ LEGAL_PRIVACY ─→ RISK_MITIGATION ─→ (운영 정책)

RUNBOOK ─→ TEST_PLAN ─→ 자율 모드 실행
```

문서가 충돌하면 **ADR > LEGAL_PRIVACY > PRD > 기타** 순으로 권위.
