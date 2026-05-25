# Architecture Improvement Status — 2026-05-25

This is the short resume file for the architecture plan series. Read this before opening any `plan*.md`. Keep it concise so a new model context never needs the full previous transcript.

## Latest Inspection

- Inspection date: 2026-05-26 KST.
- Scope inspected: local worktree and `docs/architecture-improvements/2026-05-25`.
- Verification status has been refreshed in this pass for frontend split work (`plan13a`, `plan13b`) and local pipeline pytest.
- Worktree contains many uncommitted edits and new files. Do not revert unrelated changes.
- The last interruption happened while `plan9.md` LLM routing work was being generated. The terminal reported repeated `context_length_exceeded` during remote compaction.
- 2026-05-26 follow-up: plan9/plan9b/plan10 acceptance was re-verified on the current branch.
- 2026-05-26 08:42 KST: final merge/deploy verification pass begun after code changes.
- 2026-05-26 23:43 KST: PR #1 is merged on GitHub (`MERGED`) and API smoke checks executed on production domain.

## Current Resume Point

- Resume point: `plan13c.md` completed; all architecture-improvement plans complete.

## Plan Ledger

| Plan | Status | Next Action |
|---|---|---|
| `plan1.md` | Completed (verified) | Public agency taxonomy and ADR-011 alignment complete. |
| `plan2.md` | Completed (verified) | Legal visibility filters and masking tests are in place. |
| `plan2b.md` | Completed (verified) | Capital-area elected-rank policy and non-Seoul hard stop are present. |
| `plan3.md` | Completed (verified) | Route helpers and readonly DB behavior are implemented. |
| `plan3b.md` | Completed (verified) | Route policy tests are present. |
| `plan4.md` | Completed (verified) | Public route registry/doc contract alignment is in place. |
| `plan5.md` | Completed (verified) | Agency/region registry tests are present. |
| `plan6.md` | Completed (verified) | Place-resolution policy tests and policy behavior are in place. |
| `plan7.md` | Completed (verified) | Source-pattern parsing and adapter-required stops are implemented. |
| `plan8.md` | Completed (verified) | Source artifact hashing/provenance module/tests present. |
| `plan8b.md` | Completed (verified) | R2 source storage tests and missing-env paths handled. |
| `plan9.md` | Completed (local network-free tests) | `plan10`/`plan9b` checks are complete. |
| `plan9b.md` | Completed (local network-free tests) | `plan12` prereqs now include usage/budget module as implemented. |
| `plan10.md` | Completed (local pipeline tests) | Start `plan11.md` per sequence. |
| `plan11.md` | Completed (local pipeline tests) | Start `plan12.md` per sequence. |
| `plan12.md` | Completed | `pipeline` orchestration refactor, load-batch + quality gates, and CLI handoff to runner verified by local tests. |
| `plan13.md` | Coordinator only | Do not execute directly. Use `plan13a.md` after `plan12.md`. |
| `plan13a.md` | Completed | Helpers split behind shared feature modules in `apps/web/src/features/place-explorer`. |
| `plan13b.md` | Completed | Kakao map / fallback map extracted to `apps/web/src/features/place-explorer/map`. |
| `plan13c.md` | Completed | Place Explorer panels/static pages/forms/CSS split completed after plan13b; awaiting final PR/deploy check. |

## Data Backfill Note

`memory.md` contains conflicting later records: one says Phase 2 passed with `45/52` agencies and `11197` visits, while later network-limited checks report `44/52` and `9233` visits. Do not claim final production data status without a fresh DB query.

## plan9 execution notes (2026-05-26)

- `9A` done: schema providers and parser tests added.
- `9B` done: `llm/client.py`, route defaults, and fallback behavior covered by `test_llm_client.py`.
- `9C` done: `normalizer/llm.py` now routes through `LLMClient.extract(TaskType.TABLE_NORMALIZE, ...)`.
- `9D` done: `extractor/pdf_vision.py` now routes through `LLMClient.extract(TaskType.PDF_VISION_EXTRACT, ...)` and preserves sync wrapper.
- `_repair_common_json_response` now preserves newline formatting compatibility in repaired JSON.
- Fake-provider test contract now asserts provider identity from adapter name.
- `9E` completed: `llm_usage` usage metadata/예산 가드레일 테스트 마무리.
  - Added forward migration `20260526200000_add_llm_usage_metadata.sql` for `llm_usage.thinking_tokens/task_id/status/error_code`.
  - Updated `docs/DATA_MODEL.md` and `docs/PIPELINE.md` with per-attempt 상태/예산 가드레일/레코딩 정책.
  - Updated `services/pipeline/tests/test_llm_usage.py` expectations for per-attempt 기록.

### verification run

- 2026-05-26 targeted in-repo tests (using local venv, no network):
  - `./services/pipeline/.venv/bin/python -m pytest -q tests/test_llm_schema.py tests/test_llm_client.py tests/test_pdf_vision.py`
  - result: **pass** (26 passed).
- `python3 -m compileall services/pipeline/src/public_officer_pipeline/llm/client.py services/pipeline/src/public_officer_pipeline/normalizer/llm.py services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py services/pipeline/src/public_officer_pipeline/cli.py`
  - result: pass (syntax/bytecode compile OK).
- `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests`
  - result: **pass** (149 passed).
- `pytest` in `services/pipeline` could not run in this environment:
  - `pydantic`/`selectolax` missing when using plain `python3`.
  - `npm run test:pipeline` fails due `uv` cache init permission at `/Users/lee_wonyoung/.cache/uv`.
  - `UV_CACHE_DIR=/private/tmp/uv-cache npm run test:pipeline` advances but fails on DNS/network fetching `pypi.org`.
- plan9b 단계 검증:
  - `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests/test_llm_schema.py services/pipeline/tests/test_llm_client.py services/pipeline/tests/test_llm_usage.py`
  - result: **pass** (15 passed).
  - `npm run test:pipeline` with `UV_CACHE_DIR=/private/tmp/uv-cache` fails on DNS/network access to PyPI.

- `plan9` acceptance criteria:
  - Provider HTTP removed from callers: **confirmed**.
  - Fallback tests network-free: **confirmed**.
  - Full `npm run test:pipeline`: **blocked by environment (DNS/network)**; all Python tests pass locally in repo venv.
  - `OpenAI` default model silent-call risk: **contained**. `test_openai_provider_is_not_configured_without_explicit_model` confirms no `openai` provider when all OpenAI model env vars are unset.
- `plan9b` acceptance criteria:
  - Usage record metadata, status, and budget gating: **confirmed** (`test_llm_usage.py`).
  - `OpenAI` model defaults are never silently hardcoded to `gpt-5.5`; OpenAI tasks require configured model envs.
- `plan10` acceptance criteria:
  - Shared row parsing moved into `extractor/rows.py` across migrated callers.
  - Full suite with `149 passed` confirms fixture parity.
- `plan11` acceptance criteria:
  - PDF line/whole-text parsing moved behind `extractor/pdf_text` seam.
  - `rows_from_pdf_text` now uses diagnostics-aware parse seam.
  - Added `test_pdf_text_grammars.py` covering line-winner mapping, overlap precedence, fallback routing, and no-match diagnostics.
  - `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests` confirms **153 passed** on this branch.

## Context Safety Rules

- Never paste full prior conversation history into the model.
- Never paste a full repository diff when a file path and short summary are enough.
- Keep command output in the conversation to the first actionable error or a concise pass/fail line.
- Update this file at every plan boundary, before switching threads, and before any long-running verification batch.
- If context grows large, stop at the next substep boundary and resume from this file.

## Next Exact Action
Merge/deploy handoff is now completed (PR merged). Close ledger after confirming smoke checks and recording blockers.

- 2026-05-26 finalization pass:
  - `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests/test_llm_schema.py services/pipeline/tests/test_llm_client.py services/pipeline/tests/test_pdf_vision.py` -> **pass (26)**.
  - `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests/test_llm_usage.py` -> **pass (7)**.
  - `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests` -> **pass (163)**.
  - `npm run build` -> **pass**.
  - `npm run test:pipeline` -> **blocked** by uv cache (`/Users/lee_wonyoung/.cache/uv`).
  - `UV_CACHE_DIR=/private/tmp/uv-cache npm run test:pipeline` -> **blocked** by DNS/network on `https://pypi.org/simple/selectolax/`.

- 2026-05-26 follow-up: `npm --workspace apps/web run test` and `npm run build` pass locally after `plan13c`. `npm run test:pipeline` remains blocked by environment constraints (`/Users/lee_wonyoung/.cache/uv` cache write permission and DNS resolution for `pypi.org`).

- 2026-05-26 finalization continuation:
  - `gh pr view 1` -> `state=MERGED`, `mergedAt=2026-05-25T23:42:42Z`, `changedFiles=162`.
  - `gh pr checks 1` -> `Vercel` and `Vercel Preview Comments` **pass**.
  - `npm run test:api` -> **pass** (3 files, 24 tests).
  - `npm run check:public-contracts` -> **pass**.
  - Production smoke (https://xn--ob0bo0wl1ax52a.com) checks:
    - `/` and `/about` -> `HTTP 200`.
    - `/api/v1/places/search?q=스타벅스&limit=3` -> **500 internal_error**.
    - `/api/v1/places`, `/api/v1/places?bbox=...`, `/api/v1/regions` -> **500 internal_error**.
    - `/api/v1/openapi.json` -> `404`.
    - `/openapi.json` -> `200`.
    - `/api` route on this domain does not exist (`404`).
  - `gh pr merge 1 --squash --delete-branch` no longer available (PR already merged in prior run and branch is now `main`).

### plan13c execution checkpoint (2026-05-26)

- File moves completed:
  - `apps/web/src/app/App.tsx` now routes static pages and delegates map mode to `PlaceExplorer`.
  - `apps/web/src/app/staticPages.tsx` holds all static route content.
  - `apps/web/src/features/place-explorer/PlaceExplorer.tsx` owns explorer UI state/fetch/render.
  - Panel/form/CSS split files added under `apps/web/src/features/place-explorer/`.
  - `apps/web/src/styles.css` trimmed to base shell/static styles only.
- Verification:
  - `npm --workspace apps/web run test` → pass (4 files, 12 tests).
  - `npm run build` → pass.
  - `npm run test:pipeline` → blocked by environment:
    - first: `uv` cache permission at `/Users/lee_wonyoung/.cache/uv`
    - then with `UV_CACHE_DIR=/private/tmp/uv-cache`: DNS failure fetching `https://pypi.org/simple/xlrd/`.
  - `npm run dev -- --port 5173 --host 127.0.0.1` started successfully, but localhost HTTP verification is unavailable in this sandbox via direct `curl`.

### plan10 execution kickoff (2026-05-26)

- Plan scope started: centralize duplicated row parsing for amount/date/place/user/party/preview logic in new `services/pipeline/src/public_officer_pipeline/extractor/rows.py`.
- First conversion target: `opengov_html.py` and `spreadsheet.py` (safe/common path), then partial-safe conversion of `pdf_vision.py` row constructors.
- 2026-05-26: Completed `extractor/rows.py` and migrated `opengov_html.py`, `spreadsheet.py`, and most parse-specific row constructors in `pdf_vision.py` to `build_expense_row`.
- Added new tests in `services/pipeline/tests/test_expense_rows.py` covering shared parsers (`parse_amount`, `parse_party_size`, `parse_used_at`, place formatting, build row sanitation).
- Verification: `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests` → **162 passed**.
- Environment note: full repo-level `npm run test:pipeline` remains blocked by earlier DNS/cache constraints in this workspace.

## Checkpoint Notes

- 2026-05-26: Starting `plan9` at substep 9A. Will keep changes scoped to LLM routing seams and avoid touching unrelated modules.
- 2026-05-26: Substep 9A finished; added shared parser tests and package/module scaffolding. Moving into 9B (`LLMClient`, routing defaults, and fake-provider fallback tests).
