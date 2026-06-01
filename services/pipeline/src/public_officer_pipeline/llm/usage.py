from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol

from pydantic import BaseModel
import psycopg

from public_officer_pipeline.llm.schema import TaskType
from public_officer_pipeline.models import PipelineConfigError


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
    task_id: str | None = None


class LLMUsageRecorder(Protocol):
    @abstractmethod
    async def record(self, record: LLMUsageRecord) -> None: ...

    @abstractmethod
    async def spent_today_usd(self) -> Decimal: ...


class NullLLMUsageRecorder:
    async def record(self, record: LLMUsageRecord) -> None:  # pragma: no cover - no-op
        del record

    async def spent_today_usd(self) -> Decimal:
        return Decimal("0")


MODEL_TOKEN_PRICE_USD_PER_1M: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-2.5-flash": (Decimal("1.50"), Decimal("9.00")),
    "gemini-3.5-flash": (Decimal("1.50"), Decimal("9.00")),
    "claude-haiku-4-5": (Decimal("0.80"), Decimal("2.00")),
    "claude-sonnet-4-6": (Decimal("3.00"), Decimal("15.00")),
    "claude-opus-4-7": (Decimal("15.00"), Decimal("75.00")),
    "gpt-5.5": (Decimal("3.00"), Decimal("12.00")),
}


def estimate_cost_usd(
    *,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    thinking_tokens: int | None,
) -> Decimal | None:
    prices = MODEL_TOKEN_PRICE_USD_PER_1M.get(model)
    if prices is None:
        return None
    input_rate, output_rate = prices
    input_amount = Decimal(input_tokens or 0) / Decimal("1000000")
    output_amount = Decimal(output_tokens or 0) / Decimal("1000000")
    thinking_amount = Decimal(thinking_tokens or 0) / Decimal("1000000")
    return (input_amount * input_rate) + (output_amount * output_rate) + (thinking_amount * output_rate)


def _parse_decimal(value: str | None) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PipelineConfigError(f"Invalid budget value: {value}") from exc


class PostgresLLMUsageRecorder:
    def __init__(self, *, database_url: str | None = None) -> None:
        self._database_url = database_url

    async def record(self, record: LLMUsageRecord) -> None:
        if not self._database_url:
            raise PipelineConfigError("DATABASE_URL is required for llm usage recording")
        async with await psycopg.AsyncConnection.connect(self._database_url) as conn:
            await conn.execute(
                """
                INSERT INTO public.llm_usage (
                  task_type, provider, model, input_tokens, output_tokens,
                  thinking_tokens, estimated_cost_usd, status, error_code, task_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record.task_type.value,
                    record.provider,
                    record.model,
                    record.input_tokens,
                    record.output_tokens,
                    record.thinking_tokens,
                    str(record.estimated_cost_usd) if record.estimated_cost_usd is not None else None,
                    record.status,
                    record.error_code,
                    record.task_id,
                ),
            )

    async def spent_today_usd(self) -> Decimal:
        if not self._database_url:
            raise PipelineConfigError("DATABASE_URL is required for llm usage budget checks")
        async with await psycopg.AsyncConnection.connect(self._database_url) as conn:
            cursor = await conn.execute(
                """
                SELECT COALESCE(SUM(estimated_cost_usd), 0)::text
                FROM public.llm_usage
                WHERE created_at >= date_trunc('day', now())
                """
            )
            row = await cursor.fetchone()
        if row is None or row[0] is None:
            return Decimal("0")
        if isinstance(row[0], Decimal):
            return row[0]
        if isinstance(row[0], int):
            return Decimal(row[0])
        if isinstance(row[0], str):
            return Decimal(row[0])
        return _parse_decimal(str(row[0]))


__all__ = [
    "LLMUsageRecord",
    "LLMUsageRecorder",
    "NullLLMUsageRecorder",
    "PostgresLLMUsageRecorder",
    "estimate_cost_usd",
]
