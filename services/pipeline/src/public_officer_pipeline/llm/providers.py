from __future__ import annotations

import json
import os
from json import JSONDecodeError
from typing import Any

import httpx

from public_officer_pipeline.llm.schema import (
    ExtractResult,
    LLMRetryableError,
    LLMValidationError,
    LLMUnavailableError,
    TaskType,
    _loads_json_response,
)
from public_officer_pipeline.llm.config import ReasoningConfig


ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_DEFAULT_MAX_TOKENS = 8192
ANTHROPIC_MIN_THINKING_BUDGET_TOKENS = 1024
ANTHROPIC_THINKING_RESPONSE_BUFFER_TOKENS = 1024


def _provider_http_error(provider: str, response: httpx.Response, task: TaskType) -> LLMRetryableError:
    message = ""
    try:
        body = response.json()
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or "")
    except ValueError:
        message = response.text[:500]
    suffix = f": {message}" if message else ""
    return LLMRetryableError(f"{provider} HTTP {response.status_code} for {task.value}{suffix}")


def _anthropic_thinking_budget(reasoning: ReasoningConfig | None) -> int | None:
    if reasoning is None or reasoning.anthropic_thinking_tokens is None:
        return None
    return max(
        int(reasoning.anthropic_thinking_tokens),
        ANTHROPIC_MIN_THINKING_BUDGET_TOKENS,
    )


def _anthropic_max_tokens(thinking_budget: int | None) -> int:
    if thinking_budget is None:
        return ANTHROPIC_DEFAULT_MAX_TOKENS
    return max(
        ANTHROPIC_DEFAULT_MAX_TOKENS,
        thinking_budget + ANTHROPIC_THINKING_RESPONSE_BUFFER_TOKENS,
    )


def _extract_prompt_parts(prompt: str) -> tuple[str, str, str | None]:
    system_prompt = ""
    user_prompt = prompt
    image_base64 = None

    if not prompt:
        return "", "", None

    try:
        payload = json.loads(prompt)
    except JSONDecodeError:
        return "", prompt, None

    if not isinstance(payload, dict):
        return "", prompt, None

    system_prompt = (
        payload.get("system_prompt")
        or payload.get("system")
        or payload.get("systemPrompt")
        or ""
    )
    user_prompt = (
        payload.get("user_prompt")
        or payload.get("user")
        or payload.get("prompt")
        or payload.get("text")
        or prompt
    )
    image_base64 = payload.get("image_base64")
    if not isinstance(image_base64, str) or not image_base64:
        image_base64 = None
    return str(system_prompt), str(user_prompt), image_base64


def _provider_model_by_task(
    overrides: dict[TaskType, str] | None,
    task: TaskType,
    default: str | None,
) -> str:
    if overrides is None or task not in overrides:
        if not default:
            raise LLMUnavailableError(f"LLM model for task {task.value} is not configured")
        return default
    return overrides[task]


def _openai_supports_temperature(model: str) -> bool:
    return not model.startswith("gpt-5")


class AnthropicProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_by_task: dict[TaskType, str] | None = None,
    ) -> None:
        if not api_key:
            raise LLMUnavailableError("Anthropic provider requires ANTHROPIC_API_KEY")
        self._api_key = api_key
        self.name = "anthropic"
        self.model_by_task = model_by_task or {}

    async def extract(
        self,
        *,
        task: TaskType,
        prompt: str,
        schema: dict[str, Any],
        timeout: float,
        reasoning: ReasoningConfig | None = None,
    ) -> ExtractResult:
        del schema
        system_prompt, user_prompt, image_base64 = _extract_prompt_parts(prompt)
        model = _provider_model_by_task(
            self.model_by_task,
            task,
            default=task.value if task != TaskType.TABLE_NORMALIZE else "claude-haiku-4-5",
        )

        content: list[Any] = [{"type": "text", "text": user_prompt}]
        if image_base64:
            content.insert(
                0,
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64,
                    },
                },
            )

        thinking_budget = _anthropic_thinking_budget(reasoning)
        request_payload = {
            "model": model,
            "max_tokens": _anthropic_max_tokens(thinking_budget),
            "messages": [{"role": "user", "content": content}],
        }
        if thinking_budget is not None:
            request_payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        else:
            request_payload["temperature"] = 0
        if system_prompt:
            request_payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    ANTHROPIC_ENDPOINT,
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=request_payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMRetryableError(f"Anthropic timed out: {task.value}") from exc
        except httpx.RequestError as exc:
            raise LLMRetryableError(f"Anthropic request failed: {task.value}") from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise LLMRetryableError(f"Anthropic HTTP {response.status_code} for {task.value}")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _provider_http_error("Anthropic", response, task) from exc

        body = response.json()
        text = "".join(
            block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"
        )
        try:
            parsed = _loads_json_response(text)
        except JSONDecodeError as exc:
            raise LLMValidationError(f"Anthropic returned invalid JSON for {task.value}") from exc

        usage = body.get("usage", {})
        return ExtractResult(
            payload=parsed,
            provider=self.name,
            model=model,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            thinking_tokens=usage.get("thinking_tokens"),
        )


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model_by_task: dict[TaskType, str] | None = None,
    ) -> None:
        if not api_key:
            raise LLMUnavailableError("Gemini provider requires GEMINI_API_KEY")
        self._api_key = api_key
        self.name = "gemini"
        self.model_by_task = model_by_task or {}

    async def extract(
        self,
        *,
        task: TaskType,
        prompt: str,
        schema: dict[str, Any],
        timeout: float,
        reasoning: ReasoningConfig | None = None,
    ) -> ExtractResult:
        del schema
        system_prompt, user_prompt, image_base64 = _extract_prompt_parts(prompt)
        model = _provider_model_by_task(
            self.model_by_task,
            task,
            default="gemini-2.5-flash",
        )

        parts: list[dict[str, Any]] = []
        if system_prompt:
            parts.append({"text": system_prompt})
        if image_base64:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64,
                    }
                }
            )
        if user_prompt:
            parts.append({"text": user_prompt})

        request_payload = {
            "contents": [{"parts": parts or [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            },
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    GEMINI_ENDPOINT.format(model=model),
                    params={"key": self._api_key},
                    json=request_payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMRetryableError(f"Gemini timed out: {task.value}") from exc
        except httpx.RequestError as exc:
            raise LLMRetryableError(f"Gemini request failed: {task.value}") from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise LLMRetryableError(f"Gemini HTTP {response.status_code} for {task.value}")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _provider_http_error("Gemini", response, task) from exc

        body = response.json()
        parts_payload = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts_payload)
        try:
            parsed = _loads_json_response(text)
        except JSONDecodeError as exc:
            raise LLMValidationError(f"Gemini returned invalid JSON for {task.value}") from exc

        usage = body.get("usageMetadata", {})
        return ExtractResult(
            payload=parsed,
            provider=self.name,
            model=model,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            thinking_tokens=usage.get("thinkingTokenCount"),
        )


class OpenAIProvider:
    def __init__(
        self,
        *,
        api_key: str,
        default_model: str | None = None,
        model_by_task: dict[TaskType, str] | None = None,
    ) -> None:
        if not api_key:
            raise LLMUnavailableError("OpenAI provider requires OPENAI_API_KEY")
        self._api_key = api_key
        self._default_model = default_model or os.getenv("OPENAI_MODEL")
        self.name = "openai"
        self.model_by_task = model_by_task or {}

    async def extract(
        self,
        *,
        task: TaskType,
        prompt: str,
        schema: dict[str, Any],
        timeout: float,
        reasoning: ReasoningConfig | None = None,
    ) -> ExtractResult:
        del schema
        system_prompt, user_prompt, image_base64 = _extract_prompt_parts(prompt)
        model = _provider_model_by_task(self.model_by_task, task, default=self._default_model)

        if image_base64:
            user_content: list[dict[str, Any]] = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}",
                    },
                },
            ]
        else:
            user_content = [{"type": "text", "text": user_prompt}]

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content if image_base64 else user_prompt})

        request_payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        if _openai_supports_temperature(model):
            request_payload["temperature"] = 0
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENAI_ENDPOINT,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=request_payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMRetryableError(f"OpenAI timed out: {task.value}") from exc
        except httpx.RequestError as exc:
            raise LLMRetryableError(f"OpenAI request failed: {task.value}") from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise LLMRetryableError(f"OpenAI HTTP {response.status_code} for {task.value}")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _provider_http_error("OpenAI", response, task) from exc

        body = response.json()
        choices = body.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        text = message.get("content", "")
        try:
            parsed = _loads_json_response(text)
        except JSONDecodeError as exc:
            raise LLMValidationError(f"OpenAI returned invalid JSON for {task.value}") from exc

        usage = body.get("usage", {})
        return ExtractResult(
            payload=parsed,
            provider=self.name,
            model=model,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            thinking_tokens=(
                usage.get("completion_tokens_details", {}).get("reasoning_tokens")
                if isinstance(usage.get("completion_tokens_details"), dict)
                else None
            ),
        )
