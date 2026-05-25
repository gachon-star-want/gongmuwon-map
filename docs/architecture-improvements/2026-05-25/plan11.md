# plan11.md — PDF Layout Grammar Module

## Execution Snapshot

- **Status**: Completed (local test suite verification).
- **Resume point**: Start only after plan10 is complete.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

### Completion log

- 2026-05-26: `rows_from_pdf_text` now uses `pdf_text` grammar seam (`build_default_grammars`, `parse_pdf_text_with_diagnostics`) and no longer hard-owns all parser branches.
- 2026-05-26: Added `test_pdf_text_grammars.py` for line/whole-text ordering, overlap precedence, and diagnostics.
- 2026-05-26: Verification run `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests` → **153 passed**.

## Objective

Split the 1,500+ line PDF extractor into named parser Adapters behind one PDF text parsing Seam. Current `rows_from_pdf_text` returns only rows; callers and tests cannot see which grammar matched or why parsing failed.

## Prerequisites

- plan10 should be complete. If it is not, do not move row construction into PDF grammar code; do that first.
- plan9 is optional unless vision calls are also being touched.

## Read First

- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/tests/test_pdf_vision.py`
- `services/pipeline/src/public_officer_pipeline/extractor/rows.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_text/__init__.py` (new)
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_text/parser.py` (new)
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_text/grammars.py` (new)
- `services/pipeline/tests/test_pdf_vision.py`
- new `services/pipeline/tests/test_pdf_text_grammars.py`

## Target Interface

Keep the external function:

```python
def rows_from_pdf_text(text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
    ...
```

Add internal diagnostic Interface:

```python
class PdfParseDiagnostic(BaseModel):
    grammar_name: str
    row_count: int
    failed_reason: str | None = None

class PdfParseResult(BaseModel):
    rows: list[ParsedExpenseRow]
    diagnostics: list[PdfParseDiagnostic]

class PdfTextGrammar(Protocol):
    name: str
    def parse(self, text: str, *, fallback_department: str) -> list[ParsedExpenseRow]: ...

def parse_pdf_text_with_diagnostics(text: str, *, fallback_department: str) -> PdfParseResult:
    ...
```

## Parser Ordering Rule

Preserve current fallback order exactly. Before moving code, write down the current order as constants in `parser.py`. Do not reorder grammars in this plan.

Current order to preserve:

```python
LINE_GRAMMAR_ORDER = [
    "user_address",
    "date_user_amount_place",
    "purpose_place_amount",
    "region_amount_place_purpose",
    "optional_user_place_purpose_amount",
    "user_amount_place_address_purpose",
    "user_place_purpose_amount",
    "user_amount_purpose",
    "user_no_address",
    "purpose_first",
    "generic_text_row",
]

WHOLE_TEXT_FALLBACK_ORDER = [
    "user_place_purpose_layout",
    "layout_office",
    "segmented_office",
]
```

`rows_from_pdf_text` must first run all line grammars line-by-line in `LINE_GRAMMAR_ORDER`; only if that yields zero rows may it run the whole-text fallback grammars in `WHOLE_TEXT_FALLBACK_ORDER`.

## Implementation Steps

1. Identify current parser families in `pdf_vision.py`:
   - simple printed table rows
   - purpose-first rows
   - user/address rows
   - user/no-address rows
   - date/user/amount/place rows
   - segmented office layout
   - layout office table
2. Move one family at a time into `pdf_text/grammars.py`.
3. After each family move, run `pytest tests/test_pdf_vision.py -q` from `services/pipeline`.
4. Keep vision API calls, PDF-to-text shell calls, and JSON repair in `pdf_vision.py` for now.
5. Add diagnostics after behavior is preserved.
6. Use `build_expense_row` from plan10 for new grammar code.

## Tests

Add `test_pdf_text_grammars.py`:

- each representative fixture maps to the expected grammar name.
- no-match text returns empty rows and diagnostics with failure reasons.
- overlapping grammar fixture uses the same winning grammar as before.

Run:

```bash
uv run --project services/pipeline pytest tests/test_pdf_vision.py tests/test_pdf_text_grammars.py -q
npm run test:pipeline
```

## Acceptance Criteria

- `pdf_vision.py` no longer owns every regex grammar directly.
- Parser ordering is explicit and tested.
- Adding a new PDF layout means adding a grammar Adapter, not editing unrelated parser branches.

## STOP Conditions

- If moving a grammar changes parse output for existing fixtures, stop and revert that grammar move only.
- If diagnostics require large fixture rewrites, keep diagnostics internal and report the limitation.
