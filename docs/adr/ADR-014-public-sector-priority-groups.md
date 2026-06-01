# ADR-014 — Public Sector Priority Groups

- **Status**: Accepted
- **Date**: 2026-06-01
- **Supersedes in part**: [ADR-011](ADR-011-agency-taxonomy-model.md) natural key and enum value set for non-local-government agencies.

## Context

The nationwide source registry now tracks four priority groups instead of only local governments:

- **P1**: 지방자치단체·의회 486개.
- **P2**: 중앙행정기관·헌법기관·독립국가기관 60개.
- **P3**: 2026 지정 공공기관 342개.
- **P4**: 2026.3.31 기준 지방공공기관 1,312개.

P3/P4 include many institutions with the same `gov_tier`, `branch`, `parent_region`, and `sub_region`, so ADR-011's natural key is no longer sufficient.

## Decision

Add `expansion_phase` to `agencies` with values `p1`, `p2`, `p3`, `p4`, and expose `expansion_phase_label` in public API views. Extend taxonomy values as follows:

- `gov_tier`: add `national`, `constitutional`, `public`, `local_public`.
- `branch`: add `constitutional`, `public`.
- `jurisdiction_type`: add `central_administrative_agency`, `constitutional_institution`, `independent_state_agency`, `public_institution`, `local_public_institution`.

Change the agency uniqueness key to `(gov_tier, branch, parent_region, sub_region, short_name)` with `NULLS NOT DISTINCT`. UUID primary keys remain the durable identity.

## Official Baselines

- P1: 행정안전부 공공데이터포털 17개 시도 + 226개 시·군·자치구.
- P2: 정부조직관리정보시스템 2026 정부기구도·조직도.
- P3: 잡알리오 2026 공공기관 지정현황 + 재정경제부 2026년도 공공기관 지정 자료.
- P4: 클린아이 정책자료 2026.3.31 기준 첨부. 공공데이터포털 `15114862`의 1,284/1,293 불일치 수치는 보조 근거로만 사용한다.

## Consequences

- 전국 source registry target count becomes 2,200.
- P2-P4 agencies start as `adapter_required`/`pending` until each institution's 업무추진비 원문 URL, license, and attachment access are verified.
- Existing P1 local-government IDs and public Korean labels remain stable.
