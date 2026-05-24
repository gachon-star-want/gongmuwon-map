# ADR-002 — 어댑터 전략: 전부 LLM 범용 추출

- **Status**: Accepted (단, 단일 Anthropic 의존 부분은 [ADR-009](ADR-009-multi-llm-provider-routing.md)로 superseded)
- **Date**: 2026-05-23

## Context

서울 52개 기관의 게시 양식이 HTML·PDF·HWP·XLSX로 제각각이다. 옵션:

1. **사이트별 hand-coded 어댑터** — 52개 파서, 가장 정확, 유지보수 부담 큼.
2. **하이브리드** — 정보소통광장(분량 큰 곳)만 hand-coded, 나머지 LLM.
3. **전부 LLM 범용 추출** — 일관성, 다만 LLM 비용·시간.

사용자 우선 가치: **정확성 + 속도. 토큰 비용 무제한 허용.**

## Decision

**전부 LLM 범용 추출.** Anthropic Claude로 정규화 JSON 스키마 출력.

- 1차: **Haiku 4.5** — 대량 토큰 효율
- 폴백: **Sonnet 4.6** — confidence < 0.8 또는 schema validation 실패 시
- 최종 폴백: Sonnet의 vision (스캔 PDF·OCR)

## Consequences

- 어댑터 코드 거의 0 → 새 지자체 추가 시 사람 시간 거의 0.
- LLM 호출 비용 월 $30~80 예상 (Haiku 위주).
- 모델 교체·업그레이드만으로 정확도 향상 가능.
- 마스킹 룰을 LLM 시스템 프롬프트에 박을 수 있어 보안 강화.

## Risks

- LLM 호출 한도·장애 → 다음 모델로 escalate, 그래도 실패 시 사람 검토 큐.
- 비용 폭주 가능성 → 일일 토큰 예산 모니터링.
- 환각·schema 위반 → 출력 schema validator로 한 번 더 차단.

## Related

- [ADR-001](ADR-001-data-source-strategy.md), [PIPELINE.md](../PIPELINE.md)
