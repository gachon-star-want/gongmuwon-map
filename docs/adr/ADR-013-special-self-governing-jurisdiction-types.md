# ADR-013 — 특별자치시·특별자치도 jurisdiction_type 분리

- **Status**: Accepted
- **Date**: 2026-06-01
- **Supersedes (부분)**: [ADR-011](ADR-011-agency-taxonomy-model.md)의 `jurisdiction_type` 값 목록

## Context

전국 확장에서는 세종특별자치시, 강원특별자치도, 전북특별자치도, 제주특별자치도를 기관 마스터에 넣어야 한다. ADR-011의 기존 값(`special_city`, `metro_city`, `province`)만 사용하면 세종을 광역시로, 특별자치도를 일반 도로 표시해야 하므로 한국어 서비스의 공개 라벨이 부정확해진다.

전국 기관 수 기준은 지방자치단체 243개(17개 시·도 + 226개 시·군·구)이며, 집행기관과 의회를 각각 별도 기관으로 보아 486개 기관이다. 제주 제주시·서귀포시는 이 226개 기초지자체에 포함되지 않는 행정시이므로 별도 agency/council로 만들지 않는다.

## Decision

`JurisdictionType`에 다음 값을 추가한다.

| 값 | 공개 라벨 | 적용 대상 |
|---|---|---|
| `special_self_governing_city` | `특별자치시` | 세종특별자치시 |
| `special_self_governing_province` | `특별자치도` | 강원특별자치도, 전북특별자치도, 제주특별자치도 |

기존 값은 그대로 유지한다.

| 기존 값 | 공개 라벨 |
|---|---|
| `special_city` | `특별시` |
| `metro_city` | `광역시` |
| `province` | `도` |
| `autonomous_gu` | `자치구` |
| `si` | `시` |
| `gun` | `군` |

영어 enum 값은 내부 정렬·호환용 식별자이며, API/문서/화면에는 `jurisdiction_type_label` 한국어 라벨을 함께 노출한다.

## Consequences

- 세종·강원·전북·제주 광역기관을 정확한 한국어 행정구역명으로 표시할 수 있다.
- DB CHECK 제약, `agencies_public` 뷰, API row normalization, source registry 라벨 맵을 함께 확장해야 한다.
- 제주 행정시는 별도 기초 agency로 만들지 않는다. 향후 행정시 자료를 별도 수집해야 한다면 기초지자체/council 모델이 아니라 별도 ADR로 다룬다.
