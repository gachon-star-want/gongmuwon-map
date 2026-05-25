# plan10.md — Expense Row Construction Module

## Execution Snapshot

- **Status**: Pending.
- **Resume point**: Start only after `STATUS.md` marks plan9b complete or records an explicit decision to defer plan9b.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Create a deep Expense Row Construction Module. `opengov_html.py`, `spreadsheet.py`, and `pdf_vision.py` duplicate header aliasing, date/amount parsing, party-size assembly, place/address formatting, and raw excerpt construction. `ParsedExpenseRow` is a useful data model, but not yet a deep Module.

## Prerequisites

- plan2 should be complete so row construction can call raw excerpt sanitization.
- plan9 is optional.

## Read First

- `services/pipeline/src/public_officer_pipeline/models.py`
- `services/pipeline/src/public_officer_pipeline/extractor/opengov_html.py`
- `services/pipeline/src/public_officer_pipeline/extractor/spreadsheet.py`
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/tests/test_extractor.py`
- `services/pipeline/tests/test_spreadsheet.py`
- `services/pipeline/tests/test_pdf_vision.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/extractor/rows.py` (new)
- `services/pipeline/src/public_officer_pipeline/extractor/opengov_html.py`
- `services/pipeline/src/public_officer_pipeline/extractor/spreadsheet.py`
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/tests/test_extractor.py`
- `services/pipeline/tests/test_spreadsheet.py`
- `services/pipeline/tests/test_pdf_vision.py`
- new `services/pipeline/tests/test_expense_rows.py`

## Target Interface

```python
class RawExpenseFields(BaseModel):
    department_name: str | None = None
    date_text: str | None = None
    time_text: str | None = None
    used_at: datetime | None = None
    place_name: str | None = None
    address: str | None = None
    address_hint: str | None = None
    place_text: str | None = None
    purpose: str | None = None
    amount: str | int | None = None
    amount_is_thousands: bool = False
    party_size: str | int | None = None
    user_text: str | None = None
    payment_method: str | None = None
    expense_category: str | None = None
    raw_values: list[str] = []

def build_expense_row(fields: RawExpenseFields, *, fallback_department: str) -> ParsedExpenseRow | None:
    ...

def parse_amount(value: str | int | None) -> int | None: ...
def parse_party_size(value: str | int | None) -> int | None: ...
def parse_used_at(date_text: str | None, time_text: str | None) -> datetime | None: ...
def format_place_text(name: str | None, address: str | None, place_text: str | None = None) -> str | None: ...
```

Return `None` for unusable subtotal/header rows rather than throwing, matching current extractor style.

Parsing precedence:

- `used_at` wins over `date_text` + `time_text`.
- 2-digit years in spreadsheet/PDF text use the existing rule: `00`-`69` means 2000-2069, `70`-`99` means 1970-1999.
- `amount_is_thousands=True` multiplies the parsed amount by 1000.
- `place_text` wins when it already contains an address in parentheses.
- Otherwise `place_name` + `address` / `address_hint` formats as `상호(주소)`.
- `raw_values` are joined into `raw_excerpt` and sanitized through `plan2`'s `sanitize_raw_excerpt` when that Module exists.

## Implementation Steps

1. Add `extractor/rows.py` with pure parsing/building helpers.
2. Move common amount/date/place formatting logic into this Module.
3. Convert `opengov_html.py` row parsing to produce `RawExpenseFields`.
4. Convert `spreadsheet.py` row parsing to produce `RawExpenseFields`.
5. Convert only the safest/common `pdf_vision.py` row constructors first; do not rewrite all regex grammars in one pass if it risks behavior drift.
6. Keep all public extractor function names unchanged.
7. Preserve existing output for fixtures unless tests reveal a clear bug.

## Tests

Add `test_expense_rows.py`:

- amount strings with commas parse to int.
- invalid/blank amount returns `None`.
- date + time creates expected `datetime`.
- place name + address formats as `상호(주소)`.
- existing `place_text` is preserved when provided.
- raw excerpt joins raw values and is sanitized if plan2 exists.

Run:

```bash
npm run test:pipeline
```

Golden parity requirement:

- `test_extractor.py`
- `test_spreadsheet.py`
- `test_pdf_vision.py`

must pass without weakening assertions.

## Acceptance Criteria

- Header/date/amount/place construction rules have one Module Interface.
- Extractor Adapters locate source fields; they do not own common row construction policy.
- Existing fixture behavior is preserved.

## STOP Conditions

- If converting a PDF grammar changes many existing expectations, stop and leave PDF conversion partial. Complete the remaining PDF conversion in plan11.
- If sanitizing raw excerpts changes legal policy expectations, stop and reconcile with plan2.
