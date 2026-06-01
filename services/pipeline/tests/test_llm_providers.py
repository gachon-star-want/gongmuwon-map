import httpx
import pytest

from public_officer_pipeline.llm.config import ReasoningConfig
from public_officer_pipeline.llm.providers import AnthropicProvider, OpenAIProvider
from public_officer_pipeline.llm.schema import TaskType


class _DummyAnthropicClient:
    def __init__(self, captures: list[dict], **_kwargs: object) -> None:
        self._captures = captures

    async def __aenter__(self) -> "_DummyAnthropicClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(self, _url: str, *, headers: dict, json: dict, **_kwargs: object) -> httpx.Response:
        self._captures.append({"headers": headers, "json": json})
        return httpx.Response(
            200,
            request=httpx.Request("POST", _url),
            json={
                "content": [{"type": "text", "text": '{"visits": []}'}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )


class _DummyOpenAIClient:
    def __init__(self, captures: list[dict], **_kwargs: object) -> None:
        self._captures = captures

    async def __aenter__(self) -> "_DummyOpenAIClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(self, _url: str, *, headers: dict, json: dict, **_kwargs: object) -> httpx.Response:
        self._captures.append({"headers": headers, "json": json})
        return httpx.Response(
            200,
            request=httpx.Request("POST", _url),
            json={
                "choices": [{"message": {"content": '{"rows": []}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )


@pytest.mark.asyncio
async def test_anthropic_thinking_request_uses_messages_api_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[dict] = []

    monkeypatch.setattr(
        "public_officer_pipeline.llm.providers.httpx.AsyncClient",
        lambda **kwargs: _DummyAnthropicClient(captures, **kwargs),
    )

    provider = AnthropicProvider(
        api_key="test-key",
        model_by_task={TaskType.PDF_VISION_EXTRACT: "claude-sonnet-4-20250514"},
    )

    result = await provider.extract(
        task=TaskType.PDF_VISION_EXTRACT,
        prompt="{}",
        schema={},
        timeout=1,
        reasoning=ReasoningConfig(anthropic_thinking_tokens=8192),
    )

    request_payload = captures[0]["json"]
    assert result.payload == {"visits": []}
    assert request_payload["thinking"] == {"type": "enabled", "budget_tokens": 8192}
    assert request_payload["max_tokens"] > request_payload["thinking"]["budget_tokens"]
    assert "extended_thinking" not in request_payload
    assert "temperature" not in request_payload


@pytest.mark.asyncio
async def test_anthropic_non_thinking_request_keeps_deterministic_temperature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[dict] = []

    monkeypatch.setattr(
        "public_officer_pipeline.llm.providers.httpx.AsyncClient",
        lambda **kwargs: _DummyAnthropicClient(captures, **kwargs),
    )

    provider = AnthropicProvider(
        api_key="test-key",
        model_by_task={TaskType.TABLE_NORMALIZE: "claude-haiku-4-5"},
    )

    await provider.extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="{}",
        schema={},
        timeout=1,
        reasoning=ReasoningConfig(),
    )

    request_payload = captures[0]["json"]
    assert request_payload["temperature"] == 0
    assert "thinking" not in request_payload


@pytest.mark.asyncio
async def test_openai_gpt5_request_omits_unsupported_temperature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[dict] = []

    monkeypatch.setattr(
        "public_officer_pipeline.llm.providers.httpx.AsyncClient",
        lambda **kwargs: _DummyOpenAIClient(captures, **kwargs),
    )

    provider = OpenAIProvider(
        api_key="test-key",
        model_by_task={TaskType.PDF_VISION_EXTRACT: "gpt-5.5"},
    )

    result = await provider.extract(
        task=TaskType.PDF_VISION_EXTRACT,
        prompt="{}",
        schema={},
        timeout=1,
    )

    request_payload = captures[0]["json"]
    assert result.payload == {"rows": []}
    assert request_payload["model"] == "gpt-5.5"
    assert "temperature" not in request_payload
    assert request_payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_openai_non_gpt5_request_keeps_deterministic_temperature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[dict] = []

    monkeypatch.setattr(
        "public_officer_pipeline.llm.providers.httpx.AsyncClient",
        lambda **kwargs: _DummyOpenAIClient(captures, **kwargs),
    )

    provider = OpenAIProvider(
        api_key="test-key",
        model_by_task={TaskType.TABLE_NORMALIZE: "gpt-4o-mini"},
    )

    await provider.extract(
        task=TaskType.TABLE_NORMALIZE,
        prompt="{}",
        schema={},
        timeout=1,
    )

    request_payload = captures[0]["json"]
    assert request_payload["temperature"] == 0
