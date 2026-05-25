# plan9.md — LLM Routing Module

## Execution Snapshot

- **Status**: Completed implementation; awaiting environment-dependent verification.
- **Resume point**: `plan9b.md` next, after `npm run test:pipeline` verification.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Implement the provider-routing core of ADR-009 behind one LLM Routing Module. Current code calls Anthropic directly in normalization, while PDF vision has separate Gemini/Anthropic branching. Provider choice, fallback, JSON repair, and confidence escalation should live behind one Interface.

This plan does not finish ADR-009 by itself. `plan9b.md` owns usage persistence, thinking/reasoning budget enforcement, and daily budget guardrails.

## Prerequisites

- plan2 should be complete if masking verification will use LLM routing.
- plan8 is recommended but not strictly required.

## Read First

- `docs/adr/ADR-009-multi-llm-provider-routing.md`
- `docs/PIPELINE.md` normalizer section
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/tests/test_pdf_vision.py`
- `services/pipeline/tests/test_masking.py`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/llm/__init__.py` (new)
- `services/pipeline/src/public_officer_pipeline/llm/client.py` (new)
- `services/pipeline/src/public_officer_pipeline/llm/providers.py` (new)
- `services/pipeline/src/public_officer_pipeline/llm/schema.py` (new)
- `services/pipeline/src/public_officer_pipeline/normalizer/llm.py`
- `services/pipeline/src/public_officer_pipeline/extractor/pdf_vision.py`
- `services/pipeline/tests/test_pdf_vision.py`
- new LLM routing tests

Do not persist usage to DB in this plan. Return usage metadata from provider calls so `plan9b.md` can record it without changing this Interface.

## Target Interface

```python
class TaskType(StrEnum):
    TABLE_NORMALIZE = "table_normalize"
    PDF_TEXT_EXTRACT = "pdf_text_extract"
    PDF_VISION_EXTRACT = "pdf_vision_extract"
    MASKING_VERIFY = "masking_verify"
    NAME_NORMALIZE = "name_normalize"
    SITE_ADAPTER_INFER = "site_adapter_infer"

class ExtractResult(BaseModel):
    payload: dict[str, Any]
    provider: str
    model: str
    confidence: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None

class LLMProvider(Protocol):
    async def extract(self, *, task: TaskType, prompt: str, schema: dict[str, Any], timeout: float) -> ExtractResult: ...

class LLMClient:
    async def extract(self, *, task: TaskType, prompt: str, schema: dict[str, Any], timeout: float = 30.0) -> ExtractResult: ...
```

Provider Adapters:

- Anthropic provider
- Gemini provider
- OpenAI provider stub or real provider depending on available env vars
- Fake provider for tests

## Routing Defaults

Use ADR-009 as source of truth:

- `TABLE_NORMALIZE`: Gemini first if `GEMINI_API_KEY`, then Anthropic, then OpenAI.
- `PDF_VISION_EXTRACT`: Anthropic first if `ANTHROPIC_API_KEY`, then Gemini, then OpenAI.
- `PDF_TEXT_EXTRACT`: Anthropic first, then Gemini.
- `MASKING_VERIFY`: Anthropic only unless ADR/docs are updated.
- `NAME_NORMALIZE` and `SITE_ADAPTER_INFER`: define routing config constants from ADR-009 even if no current caller uses them yet.

If a key is missing, skip that provider rather than failing until all provider options are exhausted.

## Failure And Fallback Rules

Fallback to next provider on:

- HTTP 429
- HTTP 5xx
- timeout
- invalid JSON after one local repair attempt
- schema validation failure
- average confidence below `0.8` when confidence is present

Do not fallback on:

- missing all provider keys: raise `PipelineConfigError`
- caller input error: raise immediately

## Context-Safe Substeps

Run `plan9.md` as four small sessions if needed. Update `STATUS.md` after each substep instead of relying on chat compaction.

1. **9A schema/providers**: finish `llm/schema.py`, `llm/providers.py`, and JSON parsing tests only. Do not touch normalizer or PDF vision in this substep.
2. **9B client/fallback**: add `llm/client.py`, routing defaults, fake providers, and fallback tests. Keep all tests network-free.
3. **9C normalizer caller**: convert `normalizer/llm.py` to `LLMClient.extract(TaskType.TABLE_NORMALIZE, ...)` while preserving deterministic fallback behavior.
4. **9D PDF vision caller**: convert `extractor/pdf_vision.py` to `LLMClient.extract(TaskType.PDF_VISION_EXTRACT, ...)`, then run the plan verification.

Do not start `plan9b.md` until all four substeps are complete and recorded in `STATUS.md`.

## Implementation Steps

1. Add LLM package with task types, result model, provider protocol, and client.
2. Move `_loads_json_response` into `llm/schema.py` or re-export it to preserve imports.
3. Convert `Normalizer._normalize_with_anthropic` to call `LLMClient.extract(TABLE_NORMALIZE, ...)`.
4. Convert PDF vision provider branches to call `LLMClient.extract(PDF_VISION_EXTRACT, ...)`.
5. Keep deterministic fallback behavior unchanged.
6. Preserve current prompt text unless needed to adapt to the new client.
7. Return metadata but do not require DB usage persistence yet.

## Tests

Add tests with fake providers:

- first provider succeeds.
- 429 falls back to second provider.
- invalid JSON falls back after repair fails.
- confidence below 0.8 falls back.
- missing all providers raises `PipelineConfigError`.
- `_loads_json_response` existing tests remain green.

Run:

```bash
npm run test:pipeline
```

## Acceptance Criteria

- Normalizer and PDF vision no longer call provider HTTP endpoints directly.
- Provider fallback is testable without network.
- ADR-009 routing policy lives in one Module.

## STOP Conditions

- If provider response formats cannot be normalized without changing output schemas, stop and document the exact provider incompatibility.
- If adding OpenAI real support requires a new dependency, leave OpenAI as a stub Adapter and report.
