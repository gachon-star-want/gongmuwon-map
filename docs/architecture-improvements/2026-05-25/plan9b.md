# plan9b.md — LLM Usage And Budget Guardrail

## Execution Snapshot

- **Status**: Blocked until `plan9.md` passes acceptance criteria.
- **Resume point**: Do not edit usage/budget code until `LLMClient` exists and `STATUS.md` marks plan9 complete.
- **Context budget**: Execute this plan in isolation. Do not paste full repository diffs, full test logs, or prior conversation transcripts into the model. Keep only this file, its `Read First` docs, `STATUS.md`, and the files listed under `Files To Touch`.
- **Progress recording**: Before ending or switching threads, update [STATUS.md](STATUS.md) with files changed, verification run, blockers, and the next exact resume action.
- **Large-output rule**: If a command emits more than roughly 80 lines, keep only the failing section or a short summary in the conversation; leave the full output in the terminal/session history.

## Objective

Complete the operational parts of ADR-009 after the routing Seam from `plan9.md` exists: thinking/reasoning budget configuration, per-attempt usage persistence, and daily budget guardrails.

## Prerequisites

- `plan9.md` is complete.
- If a live DB has applied the initial migration, use a forward migration instead of editing it in place.

## Read First

- `docs/adr/ADR-009-multi-llm-provider-routing.md`
- `docs/PIPELINE.md` model routing section
- `docs/DATA_MODEL.md` `llm_usage` section
- `services/pipeline/src/public_officer_pipeline/llm/client.py`
- `services/pipeline/src/public_officer_pipeline/llm/providers.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py`
- `supabase/migrations/20260523235106_initial.sql`

## Files To Touch

Primary:

- `services/pipeline/src/public_officer_pipeline/llm/config.py` (new or existing)
- `services/pipeline/src/public_officer_pipeline/llm/usage.py` (new)
- `services/pipeline/src/public_officer_pipeline/llm/client.py`
- `services/pipeline/src/public_officer_pipeline/llm/providers.py`
- `services/pipeline/src/public_officer_pipeline/loader/postgres.py` or a dedicated DB helper if created
- `services/pipeline/tests/test_llm_usage.py` (new)
- `supabase/migrations/20260523235106_initial.sql` or a new forward migration
- `docs/DATA_MODEL.md`
- `docs/PIPELINE.md`

## Schema Decision

Ensure `public.llm_usage` can store thinking tokens and per-attempt status:

```sql
ALTER TABLE public.llm_usage
  ADD COLUMN IF NOT EXISTS thinking_tokens integer,
  ADD COLUMN IF NOT EXISTS task_id text,
  ADD COLUMN IF NOT EXISTS status text CHECK (status IN ('success', 'fallback', 'error', 'skipped_budget')),
  ADD COLUMN IF NOT EXISTS error_code text;
```

If editing the initial migration is still valid, update the table definition directly. Otherwise create a forward migration named with the current timestamp.

## Target Interfaces

Create task config:

```python
class ReasoningConfig(BaseModel):
    anthropic_thinking_tokens: int | None = None
    openai_reasoning_effort: str | None = None
    gemini_thinking_level: str | None = None

class LLMTaskConfig(BaseModel):
    task: TaskType
    provider_order: list[str]
    models: dict[str, str]
    reasoning: dict[str, ReasoningConfig]
    confidence_threshold: float = 0.8
```

Create usage recorder:

```python
class LLMUsageRecord(BaseModel):
    task_type: TaskType
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    estimated_cost_usd: Decimal | None = None
    status: Literal["success", "fallback", "error", "skipped_budget"]
    error_code: str | None = None

class LLMUsageRecorder(Protocol):
    async def record(self, record: LLMUsageRecord) -> None: ...
    async def spent_today_usd(self) -> Decimal: ...
```

Implement:

- `NullLLMUsageRecorder` for tests/local no-DB runs.
- `PostgresLLMUsageRecorder` using `DATABASE_URL`.

## Budget Rules

- Read `LLM_BUDGET_DAILY_USD`; default to no budget cap only in local/test when unset.
- Before each provider attempt, call `spent_today_usd()`.
- If spent amount is greater than or equal to budget:
  - record `status="skipped_budget"` for the planned attempt.
  - choose the cheapest configured provider for that task if available and not already tried.
  - if no cheaper provider is available, raise `PipelineConfigError("LLM daily budget exceeded")`.
- Record every provider attempt, including failures that trigger fallback.

## Reasoning Budget Rules

Provider Adapters must receive task-level reasoning settings:

- Anthropic: map `anthropic_thinking_tokens=None` to no extended thinking; otherwise send the provider-specific extended-thinking parameter.
- OpenAI: send `reasoning.effort`.
- Gemini: send `thinking_level`.

Do not let callers pass arbitrary reasoning settings per request; they choose only `TaskType`.

## Tests

Add tests with fake providers and fake usage recorder:

- Each `TaskType` has a config matching ADR-009 provider order and reasoning values.
- Successful provider call records `status="success"` and token metadata.
- 429/5xx fallback records the first attempt as `fallback` or `error` and the second as `success`.
- Budget exceeded before first attempt raises `PipelineConfigError` unless a cheaper fallback is configured.
- Thinking tokens are stored in `LLMUsageRecord`.
- Missing `thinking_tokens` remains allowed for providers that do not report it.

Run:

```bash
npm run test:pipeline
rg -n "thinking_tokens|LLM_BUDGET_DAILY_USD|llm_usage|reasoning|thinking_level|extended_thinking" services/pipeline supabase/migrations docs/DATA_MODEL.md docs/PIPELINE.md
```

## Acceptance Criteria

- ADR-009 model/reasoning matrix exists as code, not just docs.
- Every LLM provider attempt can be audited after a run.
- Daily budget cap cannot be silently ignored.
- Usage tests run without network or Postgres.

## STOP Conditions

- If provider SDK/HTTP response formats do not expose token fields consistently, record the available fields and leave unknown fields as `None`; do not invent usage numbers.
- If adding usage persistence couples `LLMClient` directly to Postgres in a way that breaks pure tests, stop and introduce the recorder Protocol.
- If the DB schema is already applied live, do not edit the initial migration in place.
