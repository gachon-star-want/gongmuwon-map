from __future__ import annotations

import os
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any, Literal
from uuid import uuid4

from public_officer_pipeline.llm.config import (
    LLMTaskConfig,
    _has_openai_model,
    cheapest_provider,
    default_task_configs,
)
from public_officer_pipeline.llm.providers import AnthropicProvider, GeminiProvider, OpenAIProvider
from public_officer_pipeline.llm.schema import (
    ExtractResult,
    LLMProvider,
    LLMRetryableError,
    LLMUnavailableError,
    LLMValidationError,
    TaskType,
)
from public_officer_pipeline.llm.usage import (
    LLMUsageRecord,
    LLMUsageRecorder,
    NullLLMUsageRecorder,
    PostgresLLMUsageRecorder,
    estimate_cost_usd,
)
from public_officer_pipeline.models import PipelineConfigError


DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_CONFIDENCE_THRESHOLD = 0.8


class LLMClient:
    def __init__(
        self,
        *,
        anthropic_api_key: str | None = None,
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
        providers: Mapping[str, LLMProvider] | None = None,
        provider_order_by_task: Mapping[TaskType, tuple[str, ...]] | None = None,
        model_by_provider: Mapping[str, Mapping[TaskType, str | None]] | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        usage_recorder: LLMUsageRecorder | None = None,
        task_configs: Mapping[TaskType, LLMTaskConfig] | None = None,
        daily_budget_usd: str | None = None,
    ) -> None:
        provider_order_mapping = (
            {task: tuple(items) for task, items in (provider_order_by_task or {}).items()}
            if provider_order_by_task is not None
            else None
        )

        self._task_configs = {
            task: config.model_copy(deep=True)
            for task, config in default_task_configs(
                model_overrides=model_by_provider,
                provider_order_by_task=provider_order_mapping,
                confidence_threshold=confidence_threshold,
            ).items()
        }
        if task_configs is not None:
            for task, config in task_configs.items():
                self._task_configs[task] = config.model_copy(deep=True)

        self._timeout = timeout
        self._usage_recorder = usage_recorder
        if self._usage_recorder is None:
            if os.getenv("DATABASE_URL"):
                self._usage_recorder = PostgresLLMUsageRecorder()
            else:
                self._usage_recorder = NullLLMUsageRecorder()

        if providers is None:
            providers = self._build_providers(
                anthropic_api_key=anthropic_api_key,
                gemini_api_key=gemini_api_key,
                openai_api_key=openai_api_key,
            )
        self._providers = dict(providers)
        raw_budget = daily_budget_usd if daily_budget_usd is not None else os.getenv("LLM_BUDGET_DAILY_USD")
        self._daily_budget_usd = _parse_budget(raw_budget)

    def _build_providers(
        self,
        *,
        anthropic_api_key: str | None,
        gemini_api_key: str | None,
        openai_api_key: str | None,
    ) -> dict[str, LLMProvider]:
        providers: dict[str, LLMProvider] = {}

        if anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"):
            providers["anthropic"] = AnthropicProvider(
                api_key=anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", ""),
                model_by_task={
                    task: config.models.get("anthropic")
                    for task, config in self._task_configs.items()
                    if config.models.get("anthropic") is not None
                },
            )
        if gemini_api_key or os.getenv("GEMINI_API_KEY"):
            providers["gemini"] = GeminiProvider(
                api_key=gemini_api_key or os.getenv("GEMINI_API_KEY", ""),
                model_by_task={
                    task: config.models.get("gemini")
                    for task, config in self._task_configs.items()
                    if config.models.get("gemini") is not None
                },
            )
        if openai_api_key or os.getenv("OPENAI_API_KEY"):
            openai_task_models = {
                task: model
                for task, model in (
                    (task, config.models.get("openai"))
                    for task, config in self._task_configs.items()
                )
                if model is not None
            }
            if openai_task_models and _has_openai_model(openai_task_models):
                providers["openai"] = OpenAIProvider(
                    api_key=openai_api_key or os.getenv("OPENAI_API_KEY", ""),
                    default_model=os.getenv("OPENAI_MODEL"),
                    model_by_task=openai_task_models,
                )
        return providers

    def _ordered_providers_for_task(self, task: TaskType) -> list[tuple[str, LLMProvider]]:
        task_config = self._task_configs.get(task)
        if task_config is None:
            return []

        providers: list[tuple[str, LLMProvider]] = []
        for provider_name in task_config.provider_order:
            provider = self._providers.get(provider_name)
            if provider is not None:
                providers.append((provider_name, provider))
        return providers

    async def extract(
        self,
        *,
        task: TaskType,
        prompt: str,
        schema: dict[str, Any],
        timeout: float | None = None,
    ) -> ExtractResult:
        task_config = self._task_configs.get(task)
        if task_config is None:
            raise PipelineConfigError(f"No routing configuration for task: {task.value}")

        provider_pairs = self._ordered_providers_for_task(task)
        if not provider_pairs:
            raise PipelineConfigError("No LLM providers are configured for this task")

        request_timeout = self._timeout if timeout is None else timeout
        provider_lookup = {name: provider for name, provider in provider_pairs}
        attempt_order = [name for name, _ in provider_pairs]
        pending_attempts = list(attempt_order)
        attempted: set[str] = set()

        task_id = uuid4().hex
        last_error: Exception | None = None

        while pending_attempts:
            planned_provider = pending_attempts.pop(0)
            active_provider = planned_provider
            active_provider_task = provider_lookup.get(planned_provider)
            if active_provider_task is None:
                continue

            if self._daily_budget_usd is not None:
                spent = await self._usage_recorder.spent_today_usd()
                if spent >= self._daily_budget_usd:
                    await self._record_attempt(
                        task=task,
                        task_id=task_id,
                        provider_name=planned_provider,
                        result=ExtractResult(
                            payload={},
                            provider=planned_provider,
                            model=task_config.models.get(planned_provider, "unknown"),
                        ),
                        status="skipped_budget",
                        error_code="daily_budget_exceeded",
                    )
                    attempted.add(planned_provider)

                    fallback_provider = cheapest_provider(attempt_order, attempted)
                    if fallback_provider is None:
                        raise PipelineConfigError("LLM daily budget exceeded")
                    if fallback_provider in pending_attempts:
                        pending_attempts.remove(fallback_provider)
                    active_provider = fallback_provider
                    active_provider_task = provider_lookup.get(active_provider)
                    if active_provider_task is None:
                        raise PipelineConfigError("LLM daily budget exceeded")

            attempted.add(active_provider)
            reasoning = task_config.reasoning.get(active_provider, None)

            try:
                result = await active_provider_task.extract(
                    task=task,
                    prompt=prompt,
                    schema=schema,
                    timeout=request_timeout,
                    reasoning=reasoning,
                )
            except (LLMValidationError, LLMRetryableError) as exc:
                last_error = exc
                status = "fallback" if pending_attempts else "error"
                await self._record_attempt(
                    task=task,
                    task_id=task_id,
                    provider_name=active_provider,
                    result=ExtractResult(
                        payload={},
                        provider=active_provider,
                        model=task_config.models.get(active_provider, "unknown"),
                    ),
                    status=status,
                    error_code=type(exc).__name__,
                )
                if not pending_attempts:
                    break
                continue
            except LLMUnavailableError:
                last_error = LLMUnavailableError(f"LLM provider {active_provider} is unavailable")
                status = "fallback" if pending_attempts else "error"
                await self._record_attempt(
                    task=task,
                    task_id=task_id,
                    provider_name=active_provider,
                    result=ExtractResult(
                        payload={},
                        provider=active_provider,
                        model=task_config.models.get(active_provider, "unknown"),
                    ),
                    status=status,
                    error_code="unavailable",
                )
                if not pending_attempts:
                    break
                continue
            except Exception as exc:  # pragma: no cover - provider integration hard-fail
                last_error = exc
                await self._record_attempt(
                    task=task,
                    task_id=task_id,
                    provider_name=active_provider,
                    result=ExtractResult(
                        payload={},
                        provider=active_provider,
                        model=task_config.models.get(active_provider, "unknown"),
                    ),
                    status="error",
                    error_code=type(exc).__name__,
                )
                raise

            validated_payload = _validate_payload(result.payload, schema)
            result = result.model_copy(update={"payload": validated_payload})
            confidence = _average_confidence(result.payload)
            has_next_attempt = bool(pending_attempts)

            if confidence is not None and confidence < task_config.confidence_threshold:
                if has_next_attempt:
                    last_error = LLMValidationError(
                        f"Average confidence {confidence:.3f} below threshold "
                        f"{task_config.confidence_threshold:.1f} from {active_provider}"
                    )
                    await self._record_attempt(
                        task=task,
                        task_id=task_id,
                        provider_name=active_provider,
                        result=result,
                        status="fallback",
                        error_code="low_confidence",
                    )
                    continue
                await self._record_attempt(
                    task=task,
                    task_id=task_id,
                    provider_name=active_provider,
                    result=result,
                    status="error",
                    error_code="low_confidence",
                )
                raise PipelineConfigError(
                    f"Average confidence {confidence:.3f} below threshold "
                    f"{task_config.confidence_threshold:.1f} from {active_provider}"
                )

            if confidence is not None:
                result = result.model_copy(update={"confidence": confidence})
            await self._record_attempt(
                task=task,
                task_id=task_id,
                provider_name=active_provider,
                result=result,
                status="success",
                error_code=None,
            )
            return result

        if last_error is None:
            raise PipelineConfigError("No usable LLM providers available for this task")
        if not isinstance(last_error, PipelineConfigError):
            raise PipelineConfigError(f"LLM extraction failed: {last_error}")
        raise last_error

    async def _record_attempt(
        self,
        *,
        task: TaskType,
        task_id: str,
        provider_name: str,
        result: ExtractResult,
        status: Literal["success", "fallback", "error", "skipped_budget"],
        error_code: str | None,
    ) -> None:
        record = LLMUsageRecord(
            task_type=task,
            provider=provider_name,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            thinking_tokens=result.thinking_tokens,
            estimated_cost_usd=estimate_cost_usd(
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                thinking_tokens=result.thinking_tokens,
            ),
            status=status,
            error_code=error_code,
            task_id=task_id,
        )
        await self._usage_recorder.record(record)


def _average_confidence(payload: dict[str, Any]) -> float | None:
    raw_confidence = payload.get("confidence")
    if isinstance(raw_confidence, (int, float)):
        return float(raw_confidence)

    confidence_values: list[float] = []
    visits = payload.get("visits")
    if isinstance(visits, list):
        for row in visits:
            if isinstance(row, dict):
                row_confidence = row.get("confidence")
                if isinstance(row_confidence, (int, float)):
                    confidence_values.append(float(row_confidence))

    if not confidence_values:
        return None
    return sum(confidence_values) / len(confidence_values)


def _validate_payload(payload: object, schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise LLMValidationError("LLM result payload must be a JSON object")

    required = schema.get("required")
    if isinstance(required, list):
        missing = [field for field in required if field not in payload]
        if missing:
            raise LLMValidationError(f"Schema validation failed: missing required fields {missing}")

    return payload


def _parse_budget(raw_budget: str | None) -> Decimal | None:
    if raw_budget is None:
        return None
    try:
        return Decimal(raw_budget)
    except InvalidOperation as exc:
        raise PipelineConfigError(f"Invalid LLM_BUDGET_DAILY_USD value: {raw_budget}") from exc
