import pytest

from public_officer_pipeline.llm import LLMClient
from public_officer_pipeline.llm.schema import ExtractResult, LLMRetryableError, LLMValidationError, TaskType
from public_officer_pipeline.models import PipelineConfigError


class FakeProvider:
    def __init__(self, outcomes: list[object], *, name: str) -> None:
        self.name = name
        self._outcomes = outcomes

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
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome.model_copy(update={"provider": self.name})


def _fake_result(payload: dict, provider: str = "provider", model: str = "fake-model") -> ExtractResult:
    return ExtractResult(
        payload=payload,
        provider=provider,
        model=model,
        input_tokens=1,
        output_tokens=2,
    )


@pytest.mark.asyncio
async def test_extract_uses_first_configured_provider_on_success() -> None:
    providers = {
        "anthropic": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.91},
                        ]
                    }
                )
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.50},
                        ]
                    }
                )
            ],
            name="gemini",
        ),
    }

    result = await LLMClient(
        providers=providers,
        provider_order_by_task={TaskType.TABLE_NORMALIZE: ("anthropic", "gemini")},
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "anthropic"
    assert result.confidence == 0.91
    assert result.model == "fake-model"


@pytest.mark.asyncio
async def test_extract_falls_back_on_429_like_retryable_error() -> None:
    providers = {
        "anthropic": FakeProvider(
            [
                LLMRetryableError("rate limited"),
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.94},
                        ]
                    }
                ),
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.87},
                        ]
                    }
                )
            ],
            name="gemini",
        ),
    }

    result = await LLMClient(
        providers=providers,
        provider_order_by_task={TaskType.TABLE_NORMALIZE: ("anthropic", "gemini")},
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"


@pytest.mark.asyncio
async def test_extract_falls_back_on_validation_error() -> None:
    providers = {
        "anthropic": FakeProvider(
            [
                LLMValidationError("invalid json payload"),
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.87},
                        ]
                    }
                ),
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.87},
                        ]
                    }
                )
            ],
            name="gemini",
        ),
    }

    result = await LLMClient(
        providers=providers,
        provider_order_by_task={TaskType.TABLE_NORMALIZE: ("anthropic", "gemini")},
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"


@pytest.mark.asyncio
async def test_extract_falls_back_when_confidence_below_threshold() -> None:
    providers = {
        "anthropic": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.51},
                            {"confidence": 0.55},
                        ]
                    }
                ),
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.97},
                        ]
                    }
                ),
            ],
            name="anthropic",
        ),
        "gemini": FakeProvider(
            [
                _fake_result(
                    {
                        "visits": [
                            {"confidence": 0.97},
                        ]
                    }
                )
            ],
            name="gemini",
        ),
    }

    result = await LLMClient(
        providers=providers,
        provider_order_by_task={TaskType.TABLE_NORMALIZE: ("anthropic", "gemini")},
    ).extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="prompt",
        schema={"required": ["visits"]},
    )

    assert result.provider == "gemini"


@pytest.mark.asyncio
async def test_extract_raises_without_configured_provider() -> None:
    with pytest.raises(PipelineConfigError, match="No LLM providers are configured"):
        await LLMClient(providers={}).extract(
            task=TaskType.TABLE_NORMALIZE,
            prompt="prompt",
            schema={},
        )


def test_openai_provider_is_not_configured_without_explicit_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_TABLE_NORMALIZE_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_PDF_TEXT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_NAME_NORMALIZE_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_SITE_ADAPTER_INFER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MASKING_VERIFY_MODEL", raising=False)

    client = LLMClient(
        anthropic_api_key="anthropic-key",
        openai_api_key="openai-key",
    )

    assert "openai" not in {name for name, _ in client._ordered_providers_for_task(TaskType.TABLE_NORMALIZE)}
