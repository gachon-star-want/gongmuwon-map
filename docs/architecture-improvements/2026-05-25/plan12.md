# plan12.md — Pipeline Run, Load Batch, And Quality Gate Modules

## Execution Snapshot

- **Status**: Pending.
- **Resume point**: Start only after plan11 is complete and lower-level interfaces are stable.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Deepen pipeline orchestration after lower-level Interfaces are stable. Current `cli.py` owns sequencing and passes loose parallel structures into `PostgresLoader`; loader hardcodes provenance like `extractor_model`. Docs require quality gates, but current Implementation mostly counts stats and loads outputs.

## Prerequisites

Complete these first:

- plan2 legal visibility
- plan2b capital-area legal rank policy
- plan7 source pattern
- plan8 source artifact
- plan8b R2 source storage
- plan9 LLM routing
- plan9b LLM usage and budget guardrail
- plan10 row construction
- plan6 place resolution

If any prerequisite is incomplete, do not start this plan. Stop and report the missing prerequisite. Partial orchestration refactors are not allowed because they create two competing pipeline policies.

## Read First

- `docs/PIPELINE.md`
- `docs/v2/001_capital_area_expansion/03_BACKFILL_AND_PIPELINE_PLAN.md`
- `docs/v2/001_capital_area_expansion/04_DATA_QUALITY_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `services/pipeline/src/public_officer_pipeline/models.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/pipeline/__init__.py` (new)
- `services/pipeline/src/public_officer_pipeline/pipeline/run.py` (new)
- `services/pipeline/src/public_officer_pipeline/pipeline/batch.py` (new)
- `services/pipeline/src/public_officer_pipeline/pipeline/quality.py` (new)
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- pipeline tests

## Target Interfaces

### Pipeline Run

```python
class PipelineRunConfig(BaseModel):
    since: date
    limit_pages: int
    max_posts: int
    skip_posts: int = 0
    dry_run: bool = False
    quality_mode: Literal["warn", "quarantine", "fail"] = "fail"

class PipelineRunner:
    async def run_agency(self, agency: Agency, crawler: ExpenseCrawler) -> PipelineStats:
        ...
```

### Load Batch

```python
class LoadBatch(BaseModel):
    agency: Agency
    source_url: str
    source_title: str
    source_published_at: date | None
    source_hash_sha256: str
    source_file_kind: str
    storage_path: str | None = None
    visits: list[NormalizedVisit]
    resolved_places: dict[str, ResolvedPlace]
    extractor_model: str
```

Use a stable key function for `resolved_places`; do not keep ad hoc `visit.place_raw.model_dump_json()` scattered outside the Module.

Required helper:

```python
def place_resolution_key(place_raw: PlaceRaw) -> str:
    ...
```

This helper must replace every ad hoc `visit.place_raw.model_dump_json()` key outside tests.

### Quality Gate

```python
class QualityGateResult(BaseModel):
    ok: bool
    severity: Literal["warn", "quarantine", "fail"]
    code: str
    message: str

def evaluate_batch(batch: LoadBatch) -> list[QualityGateResult]:
    ...
```

Initial gates:

- legal visibility validation passed
- no normalized visits from non-empty parsed rows
- confidence below threshold
- missing coordinate ratio above threshold
- all places unmatched

Initial thresholds:

- any `LegalVisibilityError` => `fail`
- `parsed_rows > 0 and normalized_visits == 0` => `fail`
- average confidence `< 0.8` => `fail`
- any single visit confidence `< 0.5` => `quarantine`
- missing coordinate ratio `> 0.05` => `fail`
- `visits >= 5` and all resolved places are unmatched => `fail`
- missing `storage_path` in non-dry-run without `--allow-missing-r2` => `fail`

## Implementation Steps

1. Add `pipeline/batch.py` and migrate loose loader input into `LoadBatch`.
2. Change `PostgresLoader.load` to accept `LoadBatch`.
3. Keep a temporary compatibility wrapper only if needed to make the transition small.
4. Add `pipeline/quality.py`.
5. Add `pipeline/run.py` to own the current `_run_crawler` sequence.
6. Shrink `cli.py` to:
   - parse args
   - find agency
   - choose crawler Adapter
   - instantiate `PipelineRunner`
7. Preserve command names and CLI flags.
8. Preserve existing `PipelineStats` JSON output shape.

## Tests

Add tests with fake Adapters:

- runner lists/fetches/extracts/normalizes/resolves/loads in order.
- dry-run does not call loader.
- `skip_posts` and `max_posts` are honored.
- quality mode `warn` records but loads.
- quality mode `fail` stops before load.
- loader receives a `LoadBatch` with conflict-key-compatible visits.

Run:

```bash
npm run test:pipeline
```

## Acceptance Criteria

- `cli.py` is command wiring, not pipeline policy.
- Loader Interface is a single `LoadBatch`.
- Quality gates are testable without network, LLM, Kakao, or Postgres.
- Existing CLI behavior remains compatible.

## STOP Conditions

- If changing `PostgresLoader.load` breaks many callers, add a compatibility wrapper and migrate call sites incrementally.
- If quality gates would block current production data unexpectedly, default new gates to `warn` and document the stricter mode for later rollout.
