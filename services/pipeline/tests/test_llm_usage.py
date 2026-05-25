from __future__ import annotations

from decimal import Decimal

import pytest

from public_officer_pipeline.llm import (
    LLMClient,
    LLMTaskConfig,
    ReasoningConfig,
    TaskType,
    default_task_configs,
)
from public_officer_pipeline.llm.schema import (
    ExtractResult,
    LLMRetryableError,
    LLMValidationError,
)
from public_officer_pipeline.models import PipelineConfigError
from public_officer_pipeline.llm.usage import LLMUsageRecord


class FakeProvider:
    def __init__(self, outcomes: list[object], *, name: str) -> None:
        self._outcomes = outcomes
        self.name = name
        self.calls: list[dict[str, object]] = []

    async def extract(
        self,
        *,
        task,
        prompt,
        schema,
        timeout,
        reasoning=None,
    ) -> ExtractResult:
        del task, prompt, schema, timeout
        self.calls.append({"reasoning": reasoning})
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome.model_copy(update={"provider": self.name})


class FakeUsageRecorder:
    def __init__(self, spent_today_usd: Decimal | str = "0") -> None:
        self.spent_today_usd_value = Decimal(spent_today_usd)
        self.records: list[LLMUsageRecord] = []

    async def record(self, record: LLMUsageRecord) -> None:
        self.records.append(record)

    async def spent_today_usd(self) -> Decimal:
        return self.spent_today_usd_value


def _fake_result(
    *,
    payload: dict,
    model: str = "claude-haiku-4-5",
    input_tokens: int | None = 100,
    output_tokens: int | None = 200,
    thinking_tokens: int | None = 0,
    provider: str = "provider",
) -> ExtractResult:
    return ExtractResult(
        payload=payload,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
    )


def _task_config_for(
    task: TaskType,
    *,
    provider_order: list[str],
    models: dict[str, str],
) -> LLMTaskConfig:
    return LLMTaskConfig(
        task=task,
        provider_order=provider_order,
        models=models,
        reasoning={provider: ReasoningConfig() for provider in models},
    )


def test_default_task_configs_follow_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    configs = default_task_configs()
    assert configs[TaskType.TABLE_NORMALIZE].provider_order == ["gemini", "anthropic", "openai"]
    assert (
        configs[TaskType.TABLE_NORMALIZE].reasoning["gemini"].gemini_thinking_level
        == "minimal"
    )
    assert configs[TaskType.PDF_TEXT_EXTRACT].provider_order == ["anthropic", "gemini"]
    assert (
        configs[TaskType.PDF_TEXT_EXTRACT].reasoning["anthropic"].anthropic_thinking_tokens
        is None
    )
    assert (
        configs[TaskType.PDF_TEXT_EXTRACT].reasoning["gemini"].gemini_thinking_level == "low"
    )
    assert (
        configs[TaskType.PDF_VISION_EXTRACT].reasoning["anthropic"].anthropic_thinking_tokens
        == 8192
    )
    assert (
        configs[TaskType.PDF_VISION_EXTRACT].reasoning["gemini"].gemini_thinking_level
        == "medium"
    )
    assert configs[TaskType.MASKING_VERIFY].provider_order == ["anthropic"]
    assert (
        configs[TaskType.MASKING_VERIFY].reasoning["anthropic"].anthropic_thinking_tokens
        == 16384
    )
    assert configs[TaskType.NAME_NORMALIZE].provider_order == ["anthropic", "openai"]
    assert configs[TaskType.SITE_ADAPTER_INFER].provider_order == ["anthropic", "openai"]


@pytest.mark.asyncio
async def test_extract_records_success_usage_with_thinking_tokens() -> None:
    recorder = FakeUsageRecorder()
    providers = {
        "anthropic": FakeProvider(
            [_fake_result(payload={"visits": [{"confidence": 0.91}]}, thinking_tokens=123)],
            name="anthropic",
        )
    }
    result = await LLMClient(
        providers=providers,
        task_configs={
            TaskType.TABLE_NORMALIZE: _task_config_for(
                TaskType.TABLE_NORMALIZE,
                provider_order=["anthropic"],
                models={"anthropic": "claude-haiku-4-5"},
            )
        },
        usage_recorder=recorder,
        confidence_threshold=0.8,
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
        timeout=60.0,
    )

    assert result.provider == "anthropic"
    assert len(recorder.records) == 1
    assert recorder.records[0].status == "success"
    assert recorder.records[0].provider == "anthropic"
    assert recorder.records[0].thinking_tokens == 123
    assert recorder.records[0].estimated_cost_usd is not None


@pytest.mark.asyncio
async def test_extract_records_fallback_and_success_attempts() -> None:
    recorder = FakeUsageRecorder()
    providers = {
        "anthropic": FakeProvider(
            [
                LLMRetryableError("rate limited"),
                _fake_result(payload={"visits": [{"confidence": 0.92}]}, provider="anthropic"),
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    payload={"visits": [{"confidence": 0.95}]},
                    provider="gemini",
                    model="gemini-2.5-flash",
                )
            ],
            name="gemini",
        ),
    }

    config = _task_config_for(
        TaskType.TABLE_NORMALIZE,
        provider_order=["anthropic", "gemini"],
        models={"anthropic": "claude-haiku-4-5", "gemini": "gemini-2.5-flash"},
    )

    result = await LLMClient(
        providers=providers,
        task_configs={TaskType.TABLE_NORMALIZE: config},
        usage_recorder=recorder,
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"
    assert len(recorder.records) == 2
    assert recorder.records[0].status == "fallback"
    assert recorder.records[1].status == "success"
    assert recorder.records[1].provider == "gemini"
    assert all(call["reasoning"] is not None for call in providers["anthropic"].calls)


@pytest.mark.asyncio
async def test_extract_fallback_records_429_then_success_with_second_provider() -> None:
    recorder = FakeUsageRecorder()
    providers = {
        "anthropic": FakeProvider(
            [LLMValidationError("invalid"), _fake_result(payload={"visits": [{"confidence": 0.93}]})],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    payload={"visits": [{"confidence": 0.93}]},
                    provider="gemini",
                    model="gemini-2.5-flash",
                )
            ],
            name="gemini",
        ),
    }
    config = _task_config_for(
        TaskType.PDF_TEXT_EXTRACT,
        provider_order=["anthropic", "gemini"],
        models={"anthropic": "claude-haiku-4-5", "gemini": "gemini-2.5-flash"},
    )

    result = await LLMClient(
        providers=providers,
        task_configs={TaskType.PDF_TEXT_EXTRACT: config},
        usage_recorder=recorder,
    ).extract(
        task=TaskType.PDF_TEXT_EXTRACT,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"
    assert [r.status for r in recorder.records] == ["fallback", "success"]
    assert recorder.records[0].provider == "anthropic"
    assert recorder.records[1].provider == "gemini"


@pytest.mark.asyncio
async def test_budget_exceeded_raises_without_cheaper_provider() -> None:
    recorder = FakeUsageRecorder(spent_today_usd="1")
    config = _task_config_for(
        TaskType.TABLE_NORMALIZE,
        provider_order=["anthropic"],
        models={"anthropic": "claude-haiku-4-5"},
    )

    with pytest.raises(PipelineConfigError, match="LLM daily budget exceeded"):
        await LLMClient(
            providers={
                "anthropic": FakeProvider(
                    [_fake_result(payload={"visits": [{"confidence": 0.95}]})],
                    name="anthropic",
                )
            },
            task_configs={TaskType.TABLE_NORMALIZE: config},
            usage_recorder=recorder,
            daily_budget_usd="0.5",
        ).extract(
            task=TaskType.TABLE_NORMALIZE,
            prompt="prompt",
            schema={"required": ["visits"]},
        )

    assert len(recorder.records) == 1
    assert recorder.records[0].status == "skipped_budget"
    assert recorder.records[0].provider == "anthropic"
    assert recorder.records[0].error_code == "daily_budget_exceeded"


@pytest.mark.asyncio
async def test_budget_exceeded_falls_back_to_cheapest_provider() -> None:
    recorder = FakeUsageRecorder(spent_today_usd="1")
    config = _task_config_for(
        TaskType.TABLE_NORMALIZE,
        provider_order=["anthropic", "gemini"],
        models={"anthropic": "claude-haiku-4-5", "gemini": "gemini-2.5-flash"},
    )
    providers = {
        "anthropic": FakeProvider(
            [
                _fake_result(
                    payload={"visits": [{"confidence": 0.93}]},
                    provider="anthropic",
                )
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    payload={"visits": [{"confidence": 0.93}]},
                    provider="gemini",
                    model="gemini-2.5-flash",
                )
            ],
            name="gemini",
        ),
    }

    result = await LLMClient(
        providers=providers,
        task_configs={TaskType.TABLE_NORMALIZE: config},
        usage_recorder=recorder,
        daily_budget_usd="0.5",
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"
    assert len(recorder.records) == 2
    assert recorder.records[0].status == "skipped_budget"
    assert recorder.records[0].provider == "anthropic"
    assert recorder.records[1].status == "success"
    assert recorder.records[1].provider == "gemini"


@pytest.mark.asyncio
async def test_thinking_tokens_absent_is_recorded_as_null() -> None:
    recorder = FakeUsageRecorder()
    result_provider = _fake_result(
        payload={"visits": [{"confidence": 0.99}]},
        model="claude-haiku-4-5",
        thinking_tokens=None,
    )
    providers = {
        "anthropic": FakeProvider([result_provider], name="anthropic")
    }
    config = _task_config_for(
        TaskType.NAME_NORMALIZE,
        provider_order=["anthropic"],
        models={"anthropic": "claude-haiku-4-5"},
    )

    result = await LLMClient(
        providers=providers,
        task_configs={TaskType.NAME_NORMALIZE: config},
        usage_recorder=recorder,
    ).extract(
        task=TaskType.NAME_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.model == "claude-haiku-4-5"
    assert recorder.records[0].thinking_tokens is None
