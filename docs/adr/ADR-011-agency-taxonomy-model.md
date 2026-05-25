# ADR-011 — Agency Taxonomy Model (kind → gov_tier + branch + jurisdiction_type)

- **Status**: Accepted
- **Date**: 2026-05-25
- **Supersedes (부분)**: the `agencies.kind` enum defined in [ADR-006](ADR-006-stack.md) / [DATA_MODEL.md](../DATA_MODEL.md) (the 4-value `kind` column only). All other parts of those documents stand.
- **Driven by**: [docs/v2/001_capital_area_expansion/](../v2/001_capital_area_expansion/) (capital-area expansion needs to represent 도/광역시/시/군/자치구, which the Seoul-only `kind` enum cannot).

## Context

v1 modeled every agency with a single `kind` enum:

```
kind ∈ { city_hall, city_council, gu_office, gu_council }
```

This is a Seoul-only taxonomy (특별시 + 자치구). It conflates two independent axes — **government tier** (광역 vs 기초) and **branch** (집행부 vs 의회) — into one value, and it has no place to record the actual administrative-division type. v2 adds Gyeonggi-do (a 도/province with 시 and 군) and Incheon (a 광역시/metropolitan city with 자치구 and 군). These do not fit `city_hall`/`gu_office`:

- 경기도청 / 인천광역시청 are top-level (광역) offices but are not "Seoul City Hall".
- 수원시청 (a 시) and 연천군청 (a 군) are basic-tier offices but are not Seoul "자치구 offices".

Continuing to overload `gu_office` for 시청·군청·구청 across regions would lose the 시/군/구 distinction and make region-aware queries and UI filters lossy.

## Decision

Replace the single `kind` enum with **two orthogonal enums plus one descriptive enum**:

| Field | Enum | Values | Meaning |
|---|---|---|---|
| `gov_tier` | `GovTier` | `regional`, `basic` | 광역자치단체 vs 기초자치단체. |
| `branch` | `GovBranch` | `admin`, `council` | 집행부(청) vs 의회. |
| `jurisdiction_type` | `JurisdictionType` | `special_city`, `metro_city`, `province`, `autonomous_gu`, `si`, `gun` | The administrative-division type. |

### Mapping (v1 → v2)

| Old `kind` | New `gov_tier` | New `branch` |
|---|---|---|
| `city_hall` | `regional` | `admin` |
| `city_council` | `regional` | `council` |
| `gu_office` | `basic` | `admin` |
| `gu_council` | `basic` | `council` |

`jurisdiction_type` is then backfilled per region:

| Agency example | gov_tier | branch | jurisdiction_type | parent_region | sub_region |
|---|---|---|---|---|---|
| 서울특별시청 | regional | admin | `special_city` | 서울특별시 | NULL |
| 서울특별시의회 | regional | council | `special_city` | 서울특별시 | NULL |
| 강남구청 | basic | admin | `autonomous_gu` | 서울특별시 | 강남구 |
| 강남구의회 | basic | council | `autonomous_gu` | 서울특별시 | 강남구 |
| 경기도청 | regional | admin | `province` | 경기도 | NULL |
| 경기도의회 | regional | council | `province` | 경기도 | NULL |
| 수원시청 | basic | admin | `si` | 경기도 | 수원시 |
| 연천군청 | basic | admin | `gun` | 경기도 | 연천군 |
| 인천광역시청 | regional | admin | `metro_city` | 인천광역시 | NULL |
| 인천광역시의회 | regional | council | `metro_city` | 인천광역시 | NULL |
| 인천 중구청 | basic | admin | `autonomous_gu` | 인천광역시 | 중구 |
| 인천 강화군청 | basic | admin | `gun` | 인천광역시 | 강화군 |

### Natural key

The agency natural key changes from `(kind, parent_region, sub_region)` to **`(gov_tier, branch, parent_region, sub_region)`** (NULLS NOT DISTINCT, so the regional NULL `sub_region` rows stay distinct by tier+branch). This is information-equivalent to the old key (since old `kind` = `gov_tier`+`branch`), so existing Seoul rows keep identical identity.

### `agency.id` (uuid5) keys

`agency.id` continues to be `uuid5(AGENCY_NAMESPACE, key)`. **Seoul keys are unchanged** (e.g. fixed `SEOUL_CITY_HALL_AGENCY_ID`, `"seoul_city_council"`, `"{gu}:office"`, `"{gu}:council"`) to preserve existing IDs. **New regions MUST carry a region prefix** to avoid collisions — notably 인천 중구/동구/서구 would otherwise collide with Seoul 중구/동구/서구. Convention:

- Gyeonggi: `"gyeonggi:province:office"`, `"gyeonggi:province:council"`, `"gyeonggi:{시군}:office"`, `"gyeonggi:{시군}:council"`.
- Incheon: `"incheon:metro:office"`, `"incheon:metro:council"`, `"incheon:{군구}:office"`, `"incheon:{군구}:council"`.

## Consequences

- **Lossless and additive for Seoul**: every Seoul row maps deterministically; IDs and identity keys are preserved.
- **Region-aware queries/filters become possible**: e.g. "all 군 offices", "all regional councils", "everything in 경기도".
- **Schema/code touch points** (enumerated precisely in [docs/v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](../v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md)): `models.py`, `agencies.py`, `loader/postgres.py`, the initial migration SQL (`agencies` DDL + CHECK + UNIQUE + index + `agencies_public` view), `seed.sql`, and three test files.
- **`agencies_public` view** exposes `gov_tier`, `branch`, `jurisdiction_type` instead of `kind`. Public API/front-end consumers (when built) read these three fields; v1 has no front-end consumer of `kind` yet, so the blast radius is limited to the pipeline + DB layer today.
- **Migration approach**: because v1 is still pre-production (design/implementation stage, no live operational DB per [PRD.md](../PRD.md)), the **initial migration file is edited in place** rather than adding a forward migration. If any environment has already applied the initial schema, a separate forward migration is required instead — see the spec's STOP condition.

## Alternatives Considered

- **Keep `kind`, add `jurisdiction_type` only** (reinterpret the 4 values as tier+branch composites): smaller change, fully backward-compatible, but leaves `kind` semantically overloaded and its Seoul-derived value names (`city_hall`, `gu_office`) misleading for 도/시/군. Rejected in favor of a clean two-axis model (operator preference for a proper model).
- **Explode `kind` into many values** (`province_office`, `si_council`, …): enum bloat, and still conflates the two axes. Rejected.

## Related

- [DATA_MODEL.md](../DATA_MODEL.md) — `agencies` table (to be updated to the new columns).
- [docs/v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md](../v2/001_capital_area_expansion/08_AGENCY_MODEL_IMPLEMENTATION_SPEC.md) — the exact, file-by-file implementation harness.
- [docs/v2/001_capital_area_expansion/01_SCOPE.md](../v2/001_capital_area_expansion/01_SCOPE.md) §6 — the open question this ADR resolves.
