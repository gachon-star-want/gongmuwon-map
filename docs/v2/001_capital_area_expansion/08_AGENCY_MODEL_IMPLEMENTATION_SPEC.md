# 08 — Agency Model Implementation Spec (HARNESS for the coding agent)

- **Status**: Ready to implement
- **Date**: 2026-05-25
- **Decision authority**: [ADR-011](../../adr/ADR-011-agency-taxonomy-model.md)

## 0. How to use this document

This is a **literal implementation harness**. Every value, name, mapping, and file edit you need is written here. **Do not infer, guess, or improvise.** If reality diverges from this spec (a file does not look like the "BEFORE" shown, a test fails for a reason not covered, the schema is already applied to a live DB), **STOP and report** — do not invent a workaround.

This task does TWO things, in order:
1. **Migrate the agency taxonomy** from `kind` to `gov_tier` + `branch` + `jurisdiction_type` ([ADR-011](../../adr/ADR-011-agency-taxonomy-model.md)) for the existing Seoul 52.
2. **Add the 86 new agencies** (Gyeonggi 64 + Incheon 22) as `adapter_required` stubs (no real URLs).

### Absolute rules (STOP conditions)

- **No crawling, no network calls, no DB writes, no deployment.** Code + tests only.
- **No fabricated source URLs.** New agencies get `*_required` adapters with no `listUrl`/`source_url`. Unknown stays TODO.
- **Do not touch** any file not listed in §3. In particular: no masking-rule changes, no `LEGAL_PRIVACY.md` edit, no front-end, no API.
- **Do not change Seoul's data semantics**: Seoul's 52 agencies keep identical `agency.id` values and identical natural identity. Only their tier/branch/jurisdiction representation changes (information-preserving per ADR-011).
- If the initial migration SQL **has already been applied to a real database** (i.e. editing it in place would diverge from a live schema), **STOP** — a forward migration is needed and that is out of scope here.
- After each step, run the verification in §6. If anything fails unexpectedly, **STOP and report** with the exact error.

## 1. Exact region lists (use verbatim — do not rely on memory)

### Gyeonggi-do — 31 시·군 (28 cities + 3 counties)

Cities (`jurisdiction_type = si`):
수원시, 성남시, 의정부시, 안양시, 부천시, 광명시, 평택시, 동두천시, 안산시, 고양시, 과천시, 구리시, 남양주시, 오산시, 시흥시, 군포시, 의왕시, 하남시, 용인시, 파주시, 이천시, 안성시, 김포시, 화성시, 광주시, 양주시, 포천시, 여주시.

Counties (`jurisdiction_type = gun`):
연천군, 가평군, 양평군.

Plus 경기도청 + 경기도의회. **Total Gyeonggi = 2 + 31×2 = 64.**

### Incheon — 10 군·구 (8 districts + 2 counties)

Districts (`jurisdiction_type = autonomous_gu`):
중구, 동구, 미추홀구, 연수구, 남동구, 부평구, 계양구, 서구.

Counties (`jurisdiction_type = gun`):
강화군, 옹진군.

Plus 인천광역시청 + 인천광역시의회. **Total Incheon = 2 + 10×2 = 22.**

> ⚠️ 중구, 동구, 서구 also exist in Seoul. The `agency.id` keys for Incheon MUST be region-prefixed (see §4) to avoid `uuid5` collisions with Seoul.

## 2. The new enums (exact definitions)

```python
class GovTier(StrEnum):
    REGIONAL = "regional"   # 광역자치단체 (특별시·광역시·도)
    BASIC = "basic"         # 기초자치단체 (자치구·시·군)


class GovBranch(StrEnum):
    ADMIN = "admin"         # 집행부 (청)
    COUNCIL = "council"     # 의회


class JurisdictionType(StrEnum):
    SPECIAL_CITY = "special_city"      # 특별시 (서울)
    METRO_CITY = "metro_city"          # 광역시 (인천)
    PROVINCE = "province"              # 도 (경기)
    AUTONOMOUS_GU = "autonomous_gu"    # 자치구 (서울·인천 구)
    SI = "si"                          # 시 (경기 시)
    GUN = "gun"                        # 군 (경기·인천 군)
```

`AgencyKind` is **removed**. Every reference to it is replaced per §3.

## 3. File-by-file changes

> Touch ONLY these files: `models.py`, `agencies.py`, `loader/postgres.py`, `supabase/migrations/20260523235106_initial.sql`, `supabase/seed.sql`, `tests/test_agencies.py`, `tests/test_estimate_crawler.py`, `tests/test_gncouncil_crawler.py`.

### 3.1 `services/pipeline/src/public_officer_pipeline/models.py`

- **Remove** the `AgencyKind` enum (lines 14–18).
- **Add** the three enums from §2 in its place.
- **Replace** the `Agency` model's `kind` field with three fields. BEFORE:

```python
class Agency(BaseModel):
    id: UUID = SEOUL_CITY_HALL_AGENCY_ID
    name: str = "서울특별시청"
    short_name: str = "서울시청"
    kind: AgencyKind = AgencyKind.CITY_HALL
    parent_region: str = "서울특별시"
    sub_region: str | None = None
    homepage: str = "https://opengov.seoul.go.kr/expense/list"
    source_pattern: dict[str, Any] = Field(
        default_factory=lambda: {"adapter": "seoul_opengov", "searchKeyword": "서울시본청"}
    )
```

AFTER:

```python
class Agency(BaseModel):
    id: UUID = SEOUL_CITY_HALL_AGENCY_ID
    name: str = "서울특별시청"
    short_name: str = "서울시청"
    gov_tier: GovTier = GovTier.REGIONAL
    branch: GovBranch = GovBranch.ADMIN
    jurisdiction_type: JurisdictionType = JurisdictionType.SPECIAL_CITY
    parent_region: str = "서울특별시"
    sub_region: str | None = None
    homepage: str | None = "https://opengov.seoul.go.kr/expense/list"
    source_pattern: dict[str, Any] = Field(
        default_factory=lambda: {"adapter": "seoul_opengov", "searchKeyword": "서울시본청"}
    )
```

> Note: `homepage` becomes `str | None` so new agencies with no verified homepage can be `None` (do not invent homepages).

### 3.2 `services/pipeline/src/public_officer_pipeline/agencies.py`

**(a) Update imports**: replace `AgencyKind` with `GovTier, GovBranch, JurisdictionType`.

**(b) Update `seoul_agencies()`** — replace each `kind=...` with the tier/branch/jurisdiction triple:

| Where | OLD | NEW |
|---|---|---|
| `Agency()` default (서울시청, via models.py) | `kind=CITY_HALL` | `gov_tier=REGIONAL, branch=ADMIN, jurisdiction_type=SPECIAL_CITY` (already the model default) |
| 서울시의회 | `kind=AgencyKind.CITY_COUNCIL` | `gov_tier=REGIONAL, branch=COUNCIL, jurisdiction_type=SPECIAL_CITY` |
| each 구청 (`{gu}:office`) | `kind=AgencyKind.GU_OFFICE` | `gov_tier=BASIC, branch=ADMIN, jurisdiction_type=AUTONOMOUS_GU` |
| each 구의회 (`{gu}:council`) | `kind=AgencyKind.GU_COUNCIL` | `gov_tier=BASIC, branch=COUNCIL, jurisdiction_type=AUTONOMOUS_GU` |

Keep all `agency_uuid(...)` keys, homepages, and `source_pattern`s exactly as they are. Keep `assert len(SEOUL_AGENCIES) == 52` and `assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID`.

**(c) Add `gyeonggi_agencies()`** returning 64 agencies:

- Province pair:
  - 경기도청: `id=agency_uuid("gyeonggi:province:office")`, name="경기도청", short_name="경기도청", `gov_tier=REGIONAL, branch=ADMIN, jurisdiction_type=PROVINCE`, parent_region="경기도", sub_region=None, homepage=None, source_pattern=`{"adapter": "gyeonggi_admin_required", "searchKeyword": "경기도청 업무추진비", "status": "adapter_required"}`.
  - 경기도의회: `id=agency_uuid("gyeonggi:province:council")`, name="경기도의회", short_name="경기도의회", `gov_tier=REGIONAL, branch=COUNCIL, jurisdiction_type=PROVINCE`, parent_region="경기도", sub_region=None, homepage=None, source_pattern=`{"adapter": "gyeonggi_council_required", "searchKeyword": "경기도의회 업무추진비", "status": "adapter_required"}`.
- For each of the 31 시·군 (use the §1 list; `jurisdiction_type = si` for 시, `gun` for 군):
  - office: `id=agency_uuid(f"gyeonggi:{name}:office")`, name=`f"경기도 {name}"`+청 suffix → use name=`f"경기도 {시군}"`? **No** — match the Seoul style. Seoul office name is `f"서울특별시 {gu}청"`, short_name `f"{gu}청"`. So: name=`f"경기도 {시군}청"` is wrong for 시 (수원시 → 수원시청, not 수원시청... it IS 수원시청). Use: short_name=`f"{시군}청"` (e.g. "수원시청", "연천군청"), name=`f"경기도 {시군}청"` (e.g. "경기도 수원시청"). `gov_tier=BASIC, branch=ADMIN`, `jurisdiction_type` = si/gun per list, parent_region="경기도", sub_region=`시군`, homepage=None, source_pattern=`{"adapter": "gg_office_required", "searchKeyword": f"{시군}청 업무추진비", "status": "adapter_required"}`.
  - council: `id=agency_uuid(f"gyeonggi:{name}:council")`, short_name=`f"{시군}의회"` (e.g. "수원시의회", "연천군의회"), name=`f"경기도 {시군}의회"`, `gov_tier=BASIC, branch=COUNCIL`, same `jurisdiction_type`, parent_region="경기도", sub_region=`시군`, homepage=None, source_pattern=`{"adapter": "gg_council_required", "searchKeyword": f"{시군}의회 업무추진비", "status": "adapter_required"}`.
- End with `assert len(GYEONGGI_AGENCIES) == 64` and module-level `GYEONGGI_AGENCIES = gyeonggi_agencies()`.

> ⚠️ short_name construction: for a 시 named "수원시", the office short_name is "수원시청" (append "청"), council is "수원시의회" (append "의회"). For a 군 named "연천군", office is "연천군청", council is "연천군의회". The append rule is uniform: `short_name = 시군 + "청"` / `시군 + "의회"`. Do NOT strip the 시/군 suffix.

**(d) Add `incheon_agencies()`** returning 22 agencies:

- Metro pair:
  - 인천광역시청: `id=agency_uuid("incheon:metro:office")`, name="인천광역시청", short_name="인천시청", `gov_tier=REGIONAL, branch=ADMIN, jurisdiction_type=METRO_CITY`, parent_region="인천광역시", sub_region=None, homepage=None, source_pattern=`{"adapter": "incheon_admin_required", "searchKeyword": "인천광역시청 업무추진비", "status": "adapter_required"}`.
  - 인천광역시의회: `id=agency_uuid("incheon:metro:council")`, name="인천광역시의회", short_name="인천시의회", `gov_tier=REGIONAL, branch=COUNCIL, jurisdiction_type=METRO_CITY`, parent_region="인천광역시", sub_region=None, homepage=None, source_pattern=`{"adapter": "incheon_council_required", "searchKeyword": "인천광역시의회 업무추진비", "status": "adapter_required"}`.
- For each of the 10 군·구 (use the §1 list; `jurisdiction_type = autonomous_gu` for 구, `gun` for 군):
  - office: `id=agency_uuid(f"incheon:{name}:office")`, short_name=`f"{군구}청"` (e.g. "중구청", "강화군청"), name=`f"인천광역시 {군구}청"`, `gov_tier=BASIC, branch=ADMIN`, `jurisdiction_type` per list, parent_region="인천광역시", sub_region=`군구`, homepage=None, source_pattern=`{"adapter": "ic_office_required", "searchKeyword": f"인천 {군구}청 업무추진비", "status": "adapter_required"}`.
  - council: `id=agency_uuid(f"incheon:{name}:council")`, short_name=`f"{군구}의회"`, name=`f"인천광역시 {군구}의회"`, `gov_tier=BASIC, branch=COUNCIL`, same `jurisdiction_type`, parent_region="인천광역시", sub_region=`군구`, homepage=None, source_pattern=`{"adapter": "ic_council_required", "searchKeyword": f"인천 {군구}의회 업무추진비", "status": "adapter_required"}`.
- End with `assert len(INCHEON_AGENCIES) == 22` and module-level `INCHEON_AGENCIES = incheon_agencies()`.

> ⚠️ Incheon `agency_uuid` keys MUST be prefixed `incheon:` (e.g. `"incheon:중구:office"`). The Seoul 중구 keys are `"중구:office"` / `"중구:council"`. Prefixing prevents `uuid5` collision. Likewise Gyeonggi keys are prefixed `gyeonggi:`.

**(e) Optional convenience**: add `CAPITAL_AREA_AGENCIES = SEOUL_AGENCIES + GYEONGGI_AGENCIES + INCHEON_AGENCIES` and `assert len(CAPITAL_AREA_AGENCIES) == 138`. Do not change how `SEOUL_AGENCIES` is built or exported.

### 3.3 `services/pipeline/src/public_officer_pipeline/loader/postgres.py`

In `_upsert_agency` (around lines 80–106):

- **Column list**: replace `kind` with `gov_tier, branch, jurisdiction_type`. New INSERT columns:
  `id, name, short_name, gov_tier, branch, jurisdiction_type, parent_region, sub_region, homepage, source_pattern` (now 10 columns → 10 `%s` placeholders).
- **ON CONFLICT**: change `ON CONFLICT (kind, parent_region, sub_region)` to `ON CONFLICT (gov_tier, branch, parent_region, sub_region)`.
- **Params tuple**: replace `agency.kind.value` with `agency.gov_tier.value, agency.branch.value, agency.jurisdiction_type.value` in the correct positions.

No other function in this file references `kind`.

### 3.4 `supabase/migrations/20260523235106_initial.sql`

> Edit in place (v1 is pre-production per ADR-011). If the schema is already live somewhere, STOP (see §0).

- **Line 26** — replace the `kind` column definition:
  - BEFORE: `kind text NOT NULL CHECK (kind IN ('city_hall', 'city_council', 'gu_office', 'gu_council')),`
  - AFTER (three columns):
    ```sql
    gov_tier text NOT NULL CHECK (gov_tier IN ('regional', 'basic')),
    branch text NOT NULL CHECK (branch IN ('admin', 'council')),
    jurisdiction_type text NOT NULL CHECK (jurisdiction_type IN ('special_city', 'metro_city', 'province', 'autonomous_gu', 'si', 'gun')),
    ```
- **Line 32** — `UNIQUE NULLS NOT DISTINCT (kind, parent_region, sub_region)` → `UNIQUE NULLS NOT DISTINCT (gov_tier, branch, parent_region, sub_region)`.
- **Line 35** — `CREATE INDEX agencies_kind_region ON public.agencies (kind, parent_region, sub_region);` → `CREATE INDEX agencies_tier_region ON public.agencies (gov_tier, branch, parent_region, sub_region);`
- **Line 260** (`agencies_public` view) — replace `a.kind,` with `a.gov_tier,\n  a.branch,\n  a.jurisdiction_type,`.

### 3.5 `supabase/seed.sql`

The seed inserts only 서울시청. Update it:

- Column list (line 5 area): replace `kind,` with `gov_tier,\n  branch,\n  jurisdiction_type,`.
- VALUES (line 14 area): replace `'city_hall',` with `'regional',\n  'admin',\n  'special_city',`.
- ON CONFLICT (line 20): `ON CONFLICT (kind, parent_region, sub_region)` → `ON CONFLICT (gov_tier, branch, parent_region, sub_region)`.

### 3.6 Tests

**`tests/test_agencies.py`**:
- Update import: `AgencyKind` → `GovTier, GovBranch, JurisdictionType`.
- `test_seoul_agency_master_has_expected_kinds`: rewrite to assert tier/branch counts. Expected for Seoul 52:
  - `(REGIONAL, ADMIN)` = 1, `(REGIONAL, COUNCIL)` = 1, `(BASIC, ADMIN)` = 25, `(BASIC, COUNCIL)` = 25.
  - All 52 have `jurisdiction_type` ∈ {`SPECIAL_CITY` (the 2 regional), `AUTONOMOUS_GU` (the 50 basic)}.
- `test_seoul_agency_unique_identity_keys`: change the key tuple from `(kind, parent_region, sub_region)` to `(gov_tier, branch, parent_region, sub_region)`.
- All other Seoul tests (homepages, adapters, `kind == GU_COUNCIL/GU_OFFICE` filters): replace `agency.kind == AgencyKind.GU_COUNCIL` with `agency.gov_tier == GovTier.BASIC and agency.branch == GovBranch.COUNCIL`, and `GU_OFFICE` with `BASIC + ADMIN`.
- **Add** new tests:
  - `len(GYEONGGI_AGENCIES) == 64`, `len(INCHEON_AGENCIES) == 22`, `len(CAPITAL_AREA_AGENCIES) == 138`.
  - Every Gyeonggi/Incheon agency has `source_pattern["status"] == "adapter_required"` and NO `listUrl`/`source_url` key.
  - Every Gyeonggi agency has `parent_region == "경기도"`; every Incheon agency `parent_region == "인천광역시"`.
  - Region-prefixed id uniqueness: `len({a.id for a in CAPITAL_AREA_AGENCIES}) == 138` (proves no Seoul/Incheon 중구 collision).
  - Spot-check `jurisdiction_type`: 경기도청 = `PROVINCE`, 수원시청 = `SI`, 연천군청 = `GUN`, 인천광역시청 = `METRO_CITY`, 인천 강화군청 = `GUN`, 인천 중구청 = `AUTONOMOUS_GU`.

**`tests/test_estimate_crawler.py`** (line 15) and **`tests/test_gncouncil_crawler.py`** (26 sites): replace every `kind=AgencyKind.GU_OFFICE` with `gov_tier=GovTier.BASIC, branch=GovBranch.ADMIN, jurisdiction_type=JurisdictionType.AUTONOMOUS_GU`, and every `kind=AgencyKind.GU_COUNCIL` with `gov_tier=GovTier.BASIC, branch=GovBranch.COUNCIL, jurisdiction_type=JurisdictionType.AUTONOMOUS_GU`. Update the imports in both files. (These build `Agency(...)` objects directly; the new fields are required.)

## 4. `agency_uuid` key convention (summary)

| Agency | key passed to `agency_uuid()` |
|---|---|
| Seoul City Hall | (fixed `SEOUL_CITY_HALL_AGENCY_ID`, unchanged) |
| Seoul Council | `"seoul_city_council"` (unchanged) |
| Seoul gu office/council | `"{gu}:office"` / `"{gu}:council"` (unchanged) |
| Gyeonggi province | `"gyeonggi:province:office"` / `"gyeonggi:province:council"` |
| Gyeonggi 시·군 | `"gyeonggi:{시군}:office"` / `"gyeonggi:{시군}:council"` |
| Incheon metro | `"incheon:metro:office"` / `"incheon:metro:council"` |
| Incheon 군·구 | `"incheon:{군구}:office"` / `"incheon:{군구}:council"` |

## 5. DATA_MODEL.md note (documentation sync)

After code passes, update [docs/DATA_MODEL.md](../../DATA_MODEL.md) `agencies` table section so the documented schema matches: replace the `kind` column with `gov_tier`/`branch`/`jurisdiction_type`, update the UNIQUE constraint and index, and note the `agencies_public` view now exposes the three fields. This is the only doc edit allowed in this task; do not edit other docs. (If unsure, leave a clearly-marked TODO and report rather than guessing.)

## 6. Verification (run after each major step; all must pass)

```bash
cd services/pipeline
uv run python -c "from public_officer_pipeline.agencies import SEOUL_AGENCIES, GYEONGGI_AGENCIES, INCHEON_AGENCIES, CAPITAL_AREA_AGENCIES; print(len(SEOUL_AGENCIES), len(GYEONGGI_AGENCIES), len(INCHEON_AGENCIES), len(CAPITAL_AREA_AGENCIES))"
# expect: 52 64 22 138

uv run python -c "from public_officer_pipeline.agencies import CAPITAL_AREA_AGENCIES as A; print(len({a.id for a in A}))"
# expect: 138  (no uuid5 collisions)

uv run pytest tests/test_agencies.py tests/test_estimate_crawler.py tests/test_gncouncil_crawler.py -q
# expect: all pass
```

Also confirm there are **zero** remaining references to `AgencyKind` / `kind` in the touched Python files:

```bash
grep -rn "AgencyKind\|\.kind\b\|kind=" services/pipeline/src/public_officer_pipeline/ services/pipeline/tests/ || echo "clean"
```

## 7. When done — report

Print a concise summary:
- Confirm counts `52 / 64 / 22 / 138` and `138` unique ids.
- Confirm all three test files pass.
- Confirm all 86 new agencies are `adapter_required` with zero invented URLs/homepages.
- List exactly which files changed.
- Flag the `DATA_MODEL.md` update status (done / TODO).
- Report any STOP condition you hit, if any.
