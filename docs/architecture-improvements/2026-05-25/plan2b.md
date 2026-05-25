# plan2b.md — Capital-Area Legal Rank Policy

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm capital-area elected-rank policy and non-Seoul hard-stop behavior, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Extend the legal masking policy from Seoul-only ranks to the full 수도권 scope before any Gyeonggi/Incheon data can enter normalization or load. This is a policy/documentation/code sync plan, not a crawler or data-load plan.

## Prerequisites

- `plan2.md` is complete.
- `LEGAL_PRIVACY.md` remains the final authority. If the operator wants a different disclosure policy than the one below, stop and update the legal docs first.

## Read First

- `AGENTS.md`
- `docs/LEGAL_PRIVACY.md`
- `docs/PIPELINE.md` masking section
- `docs/v2/001_capital_area_expansion/06_LEGAL_AND_RISK_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/agencies.py`
- `services/pipeline/src/public_officer_pipeline/legal/visibility.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/tests/test_masking.py`

## Files To Touch

Primary:

- `docs/LEGAL_PRIVACY.md`
- `docs/PIPELINE.md`
- `docs/v2/001_capital_area_expansion/06_LEGAL_AND_RISK_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/legal/visibility.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/src/public_officer_pipeline/normalizer/rules.py`
- `services/pipeline/tests/test_masking.py`

Do not touch crawler source URLs, agency IDs, loader SQL, or public API routes in this plan.

## Policy Decision

For the 수도권 service scope, elected officials whose `representative` may be preserved as real name + rank are:

```text
서울: 시장, 구청장, 시의원, 구의원
경기: 도지사, 시장, 군수, 도의원, 시의원, 군의원
인천: 시장, 구청장, 군수, 시의원, 구의원, 군의원
```

All appointed ranks and staff-level references remain name-masked:

```text
부시장, 부지사, 부구청장, 부군수, 실장, 국장, 본부장, 과장, 팀장, 담당관, 전문위원, 주무관, 직원
```

The validator must select the allowed elected-rank set by `Agency.parent_region` and `Agency.jurisdiction_type`, not by raw source text alone.

## Target Interface Changes

Extend `public_officer_pipeline.legal.visibility`:

```python
CAPITAL_AREA_ELECTED_RANKS_BY_PARENT_REGION: dict[str, tuple[str, ...]]
APPOINTED_RANKS: tuple[str, ...]

def allowed_elected_ranks_for_agency(agency: Agency) -> tuple[str, ...]:
    ...

def validate_normalized_visit(visit: NormalizedVisit, *, agency: Agency) -> NormalizedVisit:
    ...

def validate_normalized_visits(visits: list[NormalizedVisit], *, agency: Agency) -> list[NormalizedVisit]:
    ...
```

Compatibility wrapper:

```python
def validate_seoul_normalized_visit(visit: NormalizedVisit) -> NormalizedVisit:
    ...
```

Use the compatibility wrapper only for existing tests that do not construct `Agency`.

## Implementation Steps

1. Update `LEGAL_PRIVACY.md` 표기 정책 to list the 수도권 elected ranks above.
2. Update `PIPELINE.md` masking prompt text to include the same elected-rank list and appointed-rank mask list.
3. Update `06_LEGAL_AND_RISK_PLAN.md` so the 수도권 enumeration is no longer a future prerequisite; it is implemented by this plan.
4. Update `visibility.py` to require `agency` for validation and to reject unsupported parent regions.
5. Update `normalizer/llm.py` prompt construction so the rank allowlist is generated from `allowed_elected_ranks_for_agency(agency)` once plan12 or a compatible runner passes the agency. If `Normalizer.normalize_rows` does not yet accept `agency`, add an optional `agency: Agency | None` argument and STOP when non-Seoul data calls it without one.
6. Update deterministic masking in `rules.py` so elected-name preservation uses the agency-aware allowlist. Seoul behavior must remain unchanged.
7. Add tests for Seoul, Gyeonggi, and Incheon rank behavior.

## Tests

Add tests:

- Seoul `홍길동 시장` survives; Seoul `홍길동 도지사` fails or is masked.
- Gyeonggi `홍길동 도지사`, `김철수 군수`, `박영희 도의원` survive.
- Incheon `홍길동 시장`, `김철수 군수`, `박영희 구의원` survive.
- Any region `홍길동 국장`, `김철수 과장`, `박영희 부시장`, `최민수 부지사` cannot keep `representative`.
- A non-Seoul agency passed without `agency` context is a hard error.

Run:

```bash
npm run test:pipeline
rg -n "도지사|군수|도의원|광역시의원|군의원|부지사|부군수" docs/LEGAL_PRIVACY.md docs/PIPELINE.md docs/v2/001_capital_area_expansion/06_LEGAL_AND_RISK_PLAN.md services/pipeline/src/public_officer_pipeline services/pipeline/tests
```

## Acceptance Criteria

- Legal docs, prompt text, validator constants, and tests name the same 수도권 elected-rank policy.
- Non-Seoul data cannot be normalized or loaded without agency-aware validation.
- Seoul masking behavior remains backward compatible.

## STOP Conditions

- If `LEGAL_PRIVACY.md` and `06_LEGAL_AND_RISK_PLAN.md` disagree, stop and resolve the legal policy before code changes.
- If `Normalizer.normalize_rows` cannot receive `Agency` without breaking many callers, add a temporary Seoul-only wrapper and block non-Seoul runs until plan12 passes `Agency` through the runner.
- If a source uses a rank not listed above, mask it by default and report the exact rank for legal review.
