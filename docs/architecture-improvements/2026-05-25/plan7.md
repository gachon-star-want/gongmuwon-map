# plan7.md — Source Pattern And Crawler Adapter Module

## Execution Snapshot

- **Status**: Observed as implemented in the current worktree; final verification/checkpoint still required.
- **Resume point**: Confirm source-pattern parsing and adapter-required stops, then mark complete in `STATUS.md`.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Replace raw `source_pattern: dict[str, Any]` access with a real Source Pattern Module. Current crawler Adapters directly interpret keys like `adapter`, `listUrl`, `followDetail`, `pageParam`, `pageUnitParam`, `rowsPerPage`, and `status`. That makes the Interface nearly as complex as the Implementation.

## Read First

- `docs/PIPELINE.md` crawler Adapter section
- `docs/v2/001_capital_area_expansion/02_SOURCE_REGISTRY_PLAN.md`
- `services/pipeline/src/public_officer_pipeline/agencies.py`
- `services/pipeline/src/public_officer_pipeline/models.py`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/crawler/*.py`
- `services/pipeline/tests/test_agencies.py`
- crawler tests

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/source_pattern.py` (new)
- `services/pipeline/src/public_officer_pipeline/models.py`
- `services/pipeline/src/public_officer_pipeline/cli.py`
- `services/pipeline/src/public_officer_pipeline/crawler/seoul_opengov.py`
- `services/pipeline/src/public_officer_pipeline/crawler/gncouncil.py`
- `services/pipeline/src/public_officer_pipeline/crawler/estimate.py`
- `services/pipeline/src/public_officer_pipeline/crawler/inline_table.py`
- `services/pipeline/tests/test_agencies.py`
- crawler tests that construct `Agency`

## Target Module Interface

Use Pydantic because the project already depends on it.

```python
class SourcePatternError(ValueError): ...

class SourcePattern(BaseModel):
    adapter: str
    status: str | None = None

class SeoulOpenGovPattern(SourcePattern):
    adapter: Literal["seoul_opengov"]
    searchKeyword: str
    titleIncludes: list[str] = []

class AttachmentBoardPattern(SourcePattern):
    adapter: Literal["attachment_board", "council_attachment_board"]
    listUrl: str
    fileKinds: list[str]
    followDetail: bool = False
    pageParam: str = "page"
    pageUnitParam: str | None = None
    rowsPerPage: int = 10

class EstimateListPattern(SourcePattern): ...
class InlineExpenseTablePattern(SourcePattern): ...
class AdapterRequiredPattern(SourcePattern): ...

ParsedSourcePattern = (
    SeoulOpenGovPattern
    | AttachmentBoardPattern
    | EstimateListPattern
    | InlineExpenseTablePattern
    | AdapterRequiredPattern
)

def parse_source_pattern(agency: Agency) -> ParsedSourcePattern: ...
```

`ParsedSourcePattern` can be a discriminated union or a base class hierarchy. The implementer must choose the simplest Pydantic form that passes type checking.

Required parser behavior:

- If `status == "adapter_required"`, return `AdapterRequiredPattern` even if `adapter` has a region-specific placeholder value such as `gg_office_required` or `ic_council_required`.
- Unknown non-placeholder adapters raise `SourcePatternError`.
- `fileKinds` must be a non-empty list with values in `{"pdf", "hwp", "hwpx", "xls", "xlsx", "html"}`.

## Implementation Steps

1. Add `source_pattern.py` with typed models and `parse_source_pattern`.
2. Add tests for every adapter value currently used in `SEOUL_AGENCIES`, `GYEONGGI_AGENCIES`, and `INCHEON_AGENCIES`.
3. Update `cli._run_supported_agency`:
   - call `parse_source_pattern(agency)`
   - switch on the typed pattern, not raw dict strings
   - return `unsupported_adapter` only for genuinely unknown parsed patterns
   - return `adapter_required` for `AdapterRequiredPattern` before any network call
4. Update `cli._find_agency` to iterate `CAPITAL_AREA_AGENCIES`, not `SEOUL_AGENCIES`, so Gyeonggi/Incheon placeholders can be found and rejected intentionally.
5. Update crawler constructors:
   - accept optional typed pattern or call parser internally
   - stop reading raw dict keys directly where possible
6. Preserve current defaults exactly:
   - attachment `pageParam` default `"page"`
   - attachment `rowsPerPage` default `10`
   - inline table `rowsPerPage` default `100`
7. Make `adapter_required` a first-class pattern that never attempts a network call.

## Tests

Add tests:

- all 52 Seoul agencies parse without error.
- all 86 Gyeonggi/Incheon agencies parse as `AdapterRequiredPattern`.
- missing `listUrl` for attachment board raises `SourcePatternError`.
- invalid `fileKinds` raises.
- CLI returns unsupported/adapter-required before network.

Run:

```bash
npm run test:pipeline
```

## Acceptance Criteria

- Crawler Adapters do not own raw `source_pattern` validation.
- `adapter_required` is an explicit Module state.
- Adding a crawler Adapter requires one typed pattern and one CLI mapping.

## STOP Conditions

- If Pydantic discriminated unions create more complexity than they remove, use explicit parser functions and simple models instead. Do not fight the type system.
- If any existing agency raw pattern cannot be represented, stop and report the exact agency and field.
