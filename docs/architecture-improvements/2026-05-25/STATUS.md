# Architecture Improvement Status — 2026-05-25

This is the short resume file for the architecture plan series. Read this before opening any `plan*.md`. Keep it concise so a new model context never needs the full previous transcript.

## Latest Inspection

- Inspection date: 2026-05-26 10:16 KST.
- Scope inspected: local `main`, GitHub PRs #1/#2/#3, Vercel production, public smoke endpoints, and `docs/architecture-improvements/2026-05-25`.
- All architecture-improvement plans `plan1` through `plan13c` are complete.
- PR #1 merged: `https://github.com/gachon-star-want/gongmuwon-map/pull/1` (`MERGED`, merge commit `0b47f0020990818de555ee87dc2ea25c6191cd09`, merged at `2026-05-25T23:42:42Z`).
- PR #2 merged: `https://github.com/gachon-star-want/gongmuwon-map/pull/2` (`MERGED`, merge commit `0713fba31caa8d13117ae8594f54bae07d6a1a5b`, merged at `2026-05-25T23:48:15Z`).
- PR #3 merged: `https://github.com/gachon-star-want/gongmuwon-map/pull/3` (`MERGED`, merge commit `5df1cf86186153c31d86917d53466c27c7cd9175`, merged at `2026-05-26T01:13:21Z`).
- PR #3 fixed production `/api/v1/agencies` smoke by normalizing legacy production `agencies_public.kind` rows into ADR-011 `gov_tier`/`branch`/`jurisdiction_type` fields while still supporting the newer DB view shape.
- Latest production deployment: `dpl_9YuCVcrd6mRGabYKySER4HVYS21t`, URL `https://gongmuwon-iv2vky0zu-gachon-star-wants-projects.vercel.app`, status `Ready`, alias includes `https://xn--ob0bo0wl1ax52a.com`.
- Final production smoke on `https://xn--ob0bo0wl1ax52a.com`: `/`, `/about`, `/openapi.json`, `/api/v1/regions`, `/api/v1/agencies`, `/api/v1/stats/summary`, `/api/v1/places?bbox=37.413,126.734,37.715,127.269&limit=3`, and `/api/v1/places/search?q=스타벅스&limit=3` all returned HTTP 200 with non-empty bodies.
- Guard smoke: `GET /api/closure-report` and `GET /api/takedown-request` returned 405; `OPTIONS` for both returned 204. No destructive POST was sent.
- Local verification on final `main`: `npm run build` pass; `npm --workspace apps/web run test` pass (4 files, 12 tests); `npm run test:api` pass (4 files, 27 tests); `npm run check:public-contracts` pass; `./services/pipeline/.venv/bin/pytest -q services/pipeline/tests` pass (163 tests).
- 2026-05-26 follow-up: `UV_CACHE_DIR=/private/tmp/uv-cache npm run test:pipeline` passes with network access allowed (163 tests). Default `npm run test:pipeline` remains blocked only inside the Codex sandbox because uv tries to use `/Users/lee_wonyoung/.cache/uv`, which is outside the writable roots.
- `services/pipeline/uv.lock` was synced by the successful `uv run`; the lock now includes the existing `boto3>=1.34` dependency from `services/pipeline/pyproject.toml`.

## Current Resume Point

- Resume point: all architecture-improvement plans are complete; production deploy and public smoke are verified.
- Current workstream: closed. No code, deployment, or smoke follow-up remains.

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
| `plan13c.md` | Completed (verified) | Place Explorer panels/static pages/forms/CSS split completed; final PR/deploy/smoke checks are complete. |

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

None. Final handoff is complete after this STATUS update lands on `main`.

- Final state:
  - Plan ledger: all executable plans complete and verified.
  - GitHub: PR #1, PR #2, and PR #3 merged.
  - Deployment: production `dpl_9YuCVcrd6mRGabYKySER4HVYS21t` Ready with `https://xn--ob0bo0wl1ax52a.com` alias.
  - Public smoke: required page/API matrix returned HTTP 200.
  - Private guards: POST-only routes are not open to GET and answer OPTIONS preflight.
  - Local checks: build, web tests, API tests, public contract check, and direct pipeline pytest pass.
  - Sandbox note: default `npm run test:pipeline` cannot use the home uv cache in Codex. Use `UV_CACHE_DIR=/private/tmp/uv-cache npm run test:pipeline` when running inside this sandbox.

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
