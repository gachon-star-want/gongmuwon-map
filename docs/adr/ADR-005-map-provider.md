# ADR-005 — 지도 라이브러리: 카카오맵

- **Status**: Accepted
- **Date**: 2026-05-23

## Context

지도 라이브러리 후보:

1. **카카오맵 JS API + 카카오 로컬 API**
2. **네이버맵 + 네이버 로컬**
3. **Mapbox GL JS**
4. **Leaflet + OSM**

## Decision

**카카오맵 + 카카오 로컬.**

근거:
- Entity resolution을 카카오 placeId로 잡으면 ([ADR-003](ADR-003-entity-resolution.md)) 지도 사용성도 동일 ID 기반으로 정합.
- 카카오 로컬 검색이 한국 식당 자동완성·주소·지점명 분리 정확도 최상.
- 마커 클러스터링 공식 라이브러리.
- 무료 한도: JS 지도 일 300,000회, 로컬 검색 일 30,000회 → v1 초기 충분.

## Consequences

- JS 키는 도메인 제한, REST 키는 Edge Function 안에서만 사용.
- 한도 초과 시 비즈 플랜 또는 네이버 폴백 검토.
- 지도 UI 일관성: 거지맵·cham-monimap·kofficer-guide 모두 카카오맵 사용 → 사용자 학습 비용↓.

## Alternatives Considered

- 네이버맵: 무료 한도 작음(NCP 별도 키), 거지맵이 채택 중. 폴백 옵션.
- Mapbox: 한국 POI 약함, 비용 큼.
- Leaflet+OSM: 한국 POI 거의 없음.

## Related

- [TECH_STACK.md](../TECH_STACK.md), [UI_UX.md](../UI_UX.md)
