from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from public_officer_pipeline.llm.schema import TaskType


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



MappingTaskModelOverrides = dict[TaskType, str | None]


def _default_openai_model() -> str | None:
    return os.getenv("OPENAI_MODEL")


def _build_model_map() -> dict[str, dict[TaskType, str | None]]:
    return {
        "anthropic": {
            TaskType.TABLE_NORMALIZE: os.getenv("ANTHROPIC_TABLE_NORMALIZE_MODEL", "claude-haiku-4-5"),
            TaskType.PDF_TEXT_EXTRACT: os.getenv("ANTHROPIC_PDF_TEXT_MODEL", "claude-haiku-4-5"),
            TaskType.PDF_VISION_EXTRACT: os.getenv(
                "ANTHROPIC_VISION_MODEL",
                os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            ),
            TaskType.MASKING_VERIFY: os.getenv("ANTHROPIC_MASKING_VERIFY_MODEL", "claude-sonnet-4-6"),
            TaskType.NAME_NORMALIZE: os.getenv("ANTHROPIC_NAME_NORMALIZE_MODEL", "claude-sonnet-4-6"),
            TaskType.SITE_ADAPTER_INFER: os.getenv(
                "ANTHROPIC_SITE_ADAPTER_INFER_MODEL",
                "claude-opus-4-7",
            ),
            TaskType.NEIGHBORHOOD_SUMMARY_POLISH: os.getenv(
                "ANTHROPIC_NEIGHBORHOOD_SUMMARY_MODEL", "claude-haiku-4-5"
            ),
        },
        "gemini": {
            TaskType.TABLE_NORMALIZE: os.getenv("GEMINI_TABLE_NORMALIZE_MODEL", "gemini-2.5-flash"),
            TaskType.PDF_TEXT_EXTRACT: os.getenv("GEMINI_PDF_TEXT_MODEL", "gemini-2.5-flash"),
            TaskType.PDF_VISION_EXTRACT: os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash"),
            TaskType.NAME_NORMALIZE: os.getenv("GEMINI_NAME_NORMALIZE_MODEL", "gemini-2.5-flash"),
            TaskType.SITE_ADAPTER_INFER: os.getenv("GEMINI_SITE_ADAPTER_INFER_MODEL", "gemini-2.5-flash"),
            TaskType.MASKING_VERIFY: os.getenv("GEMINI_MASKING_VERIFY_MODEL", "gemini-2.5-flash"),
            TaskType.NEIGHBORHOOD_SUMMARY_POLISH: os.getenv(
                "GEMINI_NEIGHBORHOOD_SUMMARY_MODEL", "gemini-2.5-flash"
            ),
        },
        "openai": {
            TaskType.TABLE_NORMALIZE: os.getenv("OPENAI_TABLE_NORMALIZE_MODEL", _default_openai_model()),
            TaskType.PDF_TEXT_EXTRACT: os.getenv("OPENAI_PDF_TEXT_MODEL", _default_openai_model()),
            TaskType.PDF_VISION_EXTRACT: os.getenv("OPENAI_VISION_MODEL", _default_openai_model()),
            TaskType.NAME_NORMALIZE: os.getenv("OPENAI_NAME_NORMALIZE_MODEL", _default_openai_model()),
            TaskType.SITE_ADAPTER_INFER: os.getenv("OPENAI_SITE_ADAPTER_INFER_MODEL", _default_openai_model()),
            TaskType.MASKING_VERIFY: os.getenv("OPENAI_MASKING_VERIFY_MODEL", _default_openai_model()),
            TaskType.NEIGHBORHOOD_SUMMARY_POLISH: os.getenv(
                "OPENAI_NEIGHBORHOOD_SUMMARY_MODEL", _default_openai_model()
            ),
        },
    }


def _coerce_model_overrides(
    base: dict[str, dict[TaskType, str | None]],
    overrides: Mapping[str, MappingTaskModelOverrides] | None = None,
) -> dict[str, dict[TaskType, str | None]]:
    if not overrides:
        return base

    merged = {provider: dict(values) for provider, values in base.items()}
    for provider_name, override in overrides.items():
        provider_values = merged.get(provider_name, {})
        provider_values.update(override)
        merged[provider_name] = provider_values
    return merged


def _reasoning_for_provider(
    mapping: dict[str, ReasoningConfig],
    provider_name: str,
) -> ReasoningConfig:
    return mapping.get(provider_name, ReasoningConfig())


def default_task_configs(
    *,
    model_overrides: Mapping[str, MappingTaskModelOverrides] | None = None,
    provider_order_by_task: dict[TaskType, tuple[str, ...]] | None = None,
    confidence_threshold: float = 0.8,
) -> dict[TaskType, LLMTaskConfig]:
    models = _coerce_model_overrides(_build_model_map(), model_overrides)

    configs: dict[TaskType, dict[str, Any]] = {
        TaskType.TABLE_NORMALIZE: {
            "provider_order": ["gemini", "anthropic", "openai"],
            "models": {
                "gemini": models["gemini"][TaskType.TABLE_NORMALIZE],
                "anthropic": models["anthropic"][TaskType.TABLE_NORMALIZE],
                "openai": models["openai"][TaskType.TABLE_NORMALIZE],
            },
            "reasoning": {
                "gemini": ReasoningConfig(gemini_thinking_level="minimal"),
                "anthropic": ReasoningConfig(),
                "openai": ReasoningConfig(openai_reasoning_effort="low"),
            },
        },
        TaskType.PDF_TEXT_EXTRACT: {
            "provider_order": ["anthropic", "gemini"],
            "models": {
                "anthropic": models["anthropic"][TaskType.PDF_TEXT_EXTRACT],
                "gemini": models["gemini"][TaskType.PDF_TEXT_EXTRACT],
                "openai": models["openai"][TaskType.PDF_TEXT_EXTRACT],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(),
                "gemini": ReasoningConfig(gemini_thinking_level="low"),
                "openai": ReasoningConfig(openai_reasoning_effort="low"),
            },
        },
        TaskType.PDF_VISION_EXTRACT: {
            "provider_order": ["anthropic", "gemini", "openai"],
            "models": {
                "anthropic": models["anthropic"][TaskType.PDF_VISION_EXTRACT],
                "gemini": models["gemini"][TaskType.PDF_VISION_EXTRACT],
                "openai": models["openai"][TaskType.PDF_VISION_EXTRACT],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(anthropic_thinking_tokens=8192),
                "gemini": ReasoningConfig(gemini_thinking_level="medium"),
                "openai": ReasoningConfig(openai_reasoning_effort="medium"),
            },
        },
        TaskType.MASKING_VERIFY: {
            "provider_order": ["anthropic"],
            "models": {
                "anthropic": models["anthropic"][TaskType.MASKING_VERIFY],
                "gemini": models["gemini"][TaskType.MASKING_VERIFY],
                "openai": models["openai"][TaskType.MASKING_VERIFY],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(anthropic_thinking_tokens=16384),
                "gemini": ReasoningConfig(gemini_thinking_level="high"),
                "openai": ReasoningConfig(openai_reasoning_effort="high"),
            },
        },
        TaskType.NAME_NORMALIZE: {
            "provider_order": ["anthropic", "openai"],
            "models": {
                "anthropic": models["anthropic"][TaskType.NAME_NORMALIZE],
                "gemini": models["gemini"][TaskType.NAME_NORMALIZE],
                "openai": models["openai"][TaskType.NAME_NORMALIZE],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(anthropic_thinking_tokens=4096),
                "gemini": ReasoningConfig(gemini_thinking_level="low"),
                "openai": ReasoningConfig(openai_reasoning_effort="medium"),
            },
        },
        TaskType.SITE_ADAPTER_INFER: {
            "provider_order": ["anthropic", "openai"],
            "models": {
                "anthropic": models["anthropic"][TaskType.SITE_ADAPTER_INFER],
                "gemini": models["gemini"][TaskType.SITE_ADAPTER_INFER],
                "openai": models["openai"][TaskType.SITE_ADAPTER_INFER],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(anthropic_thinking_tokens=32768),
                "gemini": ReasoningConfig(gemini_thinking_level="high"),
                "openai": ReasoningConfig(openai_reasoning_effort="high"),
            },
        },
        TaskType.NEIGHBORHOOD_SUMMARY_POLISH: {
            # 짧은 한 줄 윤색 — 저렴·빠른 모델로 충분(facts-locked, 출력 게이트로 검증)
            "provider_order": ["anthropic", "gemini"],
            "models": {
                "anthropic": models["anthropic"][TaskType.NEIGHBORHOOD_SUMMARY_POLISH],
                "gemini": models["gemini"][TaskType.NEIGHBORHOOD_SUMMARY_POLISH],
                "openai": models["openai"][TaskType.NEIGHBORHOOD_SUMMARY_POLISH],
            },
            "reasoning": {
                "anthropic": ReasoningConfig(),
                "gemini": ReasoningConfig(gemini_thinking_level="minimal"),
                "openai": ReasoningConfig(openai_reasoning_effort="low"),
            },
        },
    }

    if provider_order_by_task:
        for task, provider_order in provider_order_by_task.items():
            if task not in configs:
                continue
            configs[task]["provider_order"] = list(provider_order)

    result: dict[TaskType, LLMTaskConfig] = {}
    for task, values in configs.items():
        reasonings = values["reasoning"]
        if not isinstance(reasonings, dict):
            raise TypeError("reasoning configuration must be a dict")
        model_values = {name: model for name, model in values["models"].items() if model is not None}
        provider_order = values["provider_order"]
        effective_order = [provider for provider in provider_order if provider in model_values and model_values[provider]]
        if not effective_order:
            raise ValueError(f"No default models configured for task {task.value}")
        models_by_provider = dict(model_values)
        models_by_provider = {k: v for k, v in models_by_provider.items() if v is not None}
        result[task] = LLMTaskConfig(
            task=task,
            provider_order=effective_order,
            models=models_by_provider,
            reasoning={provider: _reasoning_for_provider(reasonings, provider) for provider in effective_order},
            confidence_threshold=confidence_threshold,
        )
    return result


PROVIDER_COST_ORDER = ("gemini", "anthropic", "openai")


def cheapest_provider(
    available: list[str],
    tried: set[str],
) -> str | None:
    for provider in PROVIDER_COST_ORDER:
        if provider in available and provider not in tried:
            return provider
    return None


def _has_openai_model(overrides: dict[TaskType, str | None]) -> bool:
    return any(value for value in overrides.values())


__all__ = [
    "ReasoningConfig",
    "LLMTaskConfig",
    "default_task_configs",
    "cheapest_provider",
    "_has_openai_model",
]
