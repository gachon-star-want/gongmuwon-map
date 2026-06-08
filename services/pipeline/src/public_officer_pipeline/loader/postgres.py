from __future__ import annotations

import atexit
import os
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from public_officer_pipeline.models import (
    Agency,
    NormalizedVisit,
    PipelineConfigError,
    ResolvedPlace,
)
from public_officer_pipeline.pipeline.batch import LoadBatch, place_resolution_key
from public_officer_pipeline.legal.visibility import validate_normalized_visits

_pools: dict[str, AsyncConnectionPool] = {}


async def _get_or_create_pool(database_url: str) -> AsyncConnectionPool:
    if database_url not in _pools:
        pool_max_size = int(os.getenv("DB_POOL_MAX_SIZE", "5"))
        pool = AsyncConnectionPool(
            database_url,
            min_size=1,
            max_size=pool_max_size,
            kwargs={"row_factory": dict_row},
        )
        await pool.open()
        _pools[database_url] = pool
    return _pools[database_url]


async def _close_all_pools() -> None:
    for pool in list(_pools.values()):
        await pool.close()
    _pools.clear()


def _atexit_close_pools() -> None:
    import asyncio as _asyncio

    try:
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            return
        loop.run_until_complete(_close_all_pools())
    except Exception:
        pass


atexit.register(_atexit_close_pools)


class PostgresLoader:
    def __init__(self, *, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise PipelineConfigError("DATABASE_URL is required for loading")

    async def load(
        self,
        batch: LoadBatch,
    ) -> tuple[int, int, int]:
        visits = validate_normalized_visits(batch.visits, agency=batch.agency)
        pool = await _get_or_create_pool(self.database_url)
        async with pool.connection() as conn:
            async with conn.transaction():
                await self._upsert_agency(conn, batch.agency)
                source_id = await self._upsert_source(
                    conn,
                    agency=batch.agency,
                    source_url=batch.source_url,
                    source_title=batch.source_title,
                    source_published_at=batch.source_published_at,
                    source_hash_sha256=batch.source_hash_sha256,
                    source_file_kind=batch.source_file_kind,
                    storage_path=batch.storage_path,
                )

                place_ids: dict[str, UUID] = {}
                for place in batch.resolved_places.values():
                    if not place.valid_place:
                        continue
                    place_ids[place.natural_key] = await self._upsert_place(conn, place)

                visit_ids = []
                for visit in visits:
                    resolved = batch.resolved_places[place_resolution_key(visit.place_raw)]
                    if resolved.natural_key not in place_ids:
                        continue
                    visit_ids.append(
                        await self._upsert_visit(
                            conn,
                            visit=visit,
                            place_id=place_ids[resolved.natural_key],
                            source_id=source_id,
                            extractor_model=batch.extractor_model,
                        )
                    )

        return 1, len(place_ids), len(visit_ids)

    async def seed_agencies(self, agencies: list[Agency]) -> int:
        pool = await _get_or_create_pool(self.database_url)
        async with pool.connection() as conn:
            async with conn.transaction():
                for agency in agencies:
                    await self._upsert_agency(conn, agency)
        return len(agencies)

    @classmethod
    async def close(cls) -> None:
        await _close_all_pools()

    async def _upsert_agency(self, conn: psycopg.AsyncConnection[Any], agency: Agency) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.agencies (
              id, name, short_name, gov_tier, branch, jurisdiction_type, expansion_phase,
              parent_region, sub_region, homepage, source_pattern
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (gov_tier, branch, parent_region, sub_region, short_name) DO UPDATE SET
              name = EXCLUDED.name,
              short_name = EXCLUDED.short_name,
              jurisdiction_type = EXCLUDED.jurisdiction_type,
              expansion_phase = EXCLUDED.expansion_phase,
              homepage = EXCLUDED.homepage,
              source_pattern = EXCLUDED.source_pattern
            RETURNING id
            """,
            (
                agency.id,
                agency.name,
                agency.short_name,
                agency.gov_tier.value,
                agency.branch.value,
                agency.jurisdiction_type.value,
                agency.expansion_phase.value,
                agency.parent_region,
                agency.sub_region,
                agency.homepage,
                Jsonb(agency.source_pattern),
            ),
        )
        return UUID(str(row["id"]))

    async def _upsert_source(
        self,
        conn: psycopg.AsyncConnection[Any],
        *,
        agency: Agency,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        source_file_kind: str,
        storage_path: str | None,
    ) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.sources (
              agency_id, url, title, published_at, file_kind, storage_path, hash_sha256
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (agency_id, hash_sha256) DO UPDATE SET
              url = EXCLUDED.url,
              title = EXCLUDED.title,
              published_at = EXCLUDED.published_at,
              storage_path = COALESCE(EXCLUDED.storage_path, public.sources.storage_path),
              fetched_at = now()
            RETURNING id
            """,
            (
                agency.id,
                source_url,
                source_title,
                source_published_at,
                source_file_kind,
                storage_path,
                source_hash_sha256,
            ),
        )
        return UUID(str(row["id"]))

    async def _upsert_place(self, conn: psycopg.AsyncConnection[Any], place: ResolvedPlace) -> UUID:
        existing_id = None
        if place.kakao_place_id:
            cursor = await conn.execute(
                "SELECT id FROM public.places WHERE kakao_place_id = %s OR natural_key = %s LIMIT 1",
                (place.kakao_place_id, place.natural_key)
            )
            row = await cursor.fetchone()
            if row:
                existing_id = UUID(str(row["id"]))
        else:
            cursor = await conn.execute(
                "SELECT id FROM public.places WHERE natural_key = %s LIMIT 1",
                (place.natural_key,)
            )
            row = await cursor.fetchone()
            if row:
                existing_id = UUID(str(row["id"]))

        if existing_id:
            await conn.execute(
                """
                UPDATE public.places
                SET
                  kakao_place_id = COALESCE(%s, kakao_place_id),
                  name = %s,
                  road_address = %s,
                  jibun_address = %s,
                  road_address_part = %s,
                  latitude = %s,
                  longitude = %s,
                  category = %s,
                  phone = %s,
                  valid_place = %s,
                  is_restaurant_like = %s,
                  is_chain = %s,
                  is_large_chain = %s,
                  chain_brand = %s,
                  chain_scale = %s,
                  updated_at = now()
                WHERE id = %s
                """,
                (
                    place.kakao_place_id,
                    place.name,
                    place.road_address,
                    place.jibun_address,
                    place.road_address_part,
                    place.latitude,
                    place.longitude,
                    place.category,
                    place.phone,
                    place.valid_place,
                    place.is_restaurant_like,
                    place.is_chain,
                    place.is_large_chain,
                    place.chain_brand,
                    place.chain_scale,
                    existing_id,
                )
            )
            return existing_id

        try:
            async with conn.transaction():
                if place.kakao_place_id:
                    row = await self._fetch_one(
                        conn,
                        """
                        INSERT INTO public.places (
                          kakao_place_id, natural_key, name, road_address, jibun_address,
                          road_address_part, latitude, longitude, category, phone,
                          valid_place, is_restaurant_like, is_chain, is_large_chain, chain_brand, chain_scale
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (kakao_place_id) DO UPDATE SET
                          natural_key = EXCLUDED.natural_key,
                          name = EXCLUDED.name,
                          road_address = EXCLUDED.road_address,
                          jibun_address = EXCLUDED.jibun_address,
                          road_address_part = EXCLUDED.road_address_part,
                          latitude = EXCLUDED.latitude,
                          longitude = EXCLUDED.longitude,
                          category = EXCLUDED.category,
                          phone = EXCLUDED.phone,
                          valid_place = EXCLUDED.valid_place,
                          is_restaurant_like = EXCLUDED.is_restaurant_like,
                          is_chain = EXCLUDED.is_chain,
                          is_large_chain = EXCLUDED.is_large_chain,
                          chain_brand = EXCLUDED.chain_brand,
                          chain_scale = EXCLUDED.chain_scale,
                          updated_at = now()
                        RETURNING id
                        """,
                        (
                            place.kakao_place_id,
                            place.natural_key,
                            place.name,
                            place.road_address,
                            place.jibun_address,
                            place.road_address_part,
                            place.latitude,
                            place.longitude,
                            place.category,
                            place.phone,
                            place.valid_place,
                            place.is_restaurant_like,
                            place.is_chain,
                            place.is_large_chain,
                            place.chain_brand,
                            place.chain_scale,
                        ),
                    )
                    return UUID(str(row["id"]))
                else:
                    row = await self._fetch_one(
                        conn,
                        """
                        INSERT INTO public.places (
                          kakao_place_id, natural_key, name, road_address, jibun_address,
                          road_address_part, latitude, longitude, category, phone,
                          valid_place, is_restaurant_like, is_chain, is_large_chain, chain_brand, chain_scale
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (natural_key) DO UPDATE SET
                          kakao_place_id = COALESCE(EXCLUDED.kakao_place_id, public.places.kakao_place_id),
                          name = EXCLUDED.name,
                          road_address = EXCLUDED.road_address,
                          jibun_address = EXCLUDED.jibun_address,
                          road_address_part = EXCLUDED.road_address_part,
                          latitude = EXCLUDED.latitude,
                          longitude = EXCLUDED.longitude,
                          category = EXCLUDED.category,
                          phone = EXCLUDED.phone,
                          valid_place = EXCLUDED.valid_place,
                          is_restaurant_like = EXCLUDED.is_restaurant_like,
                          is_chain = EXCLUDED.is_chain,
                          is_large_chain = EXCLUDED.is_large_chain,
                          chain_brand = EXCLUDED.chain_brand,
                          chain_scale = EXCLUDED.chain_scale,
                          updated_at = now()
                        RETURNING id
                        """,
                        (
                            place.kakao_place_id,
                            place.natural_key,
                            place.name,
                            place.road_address,
                            place.jibun_address,
                            place.road_address_part,
                            place.latitude,
                            place.longitude,
                            place.category,
                            place.phone,
                            place.valid_place,
                            place.is_restaurant_like,
                            place.is_chain,
                            place.is_large_chain,
                            place.chain_brand,
                            place.chain_scale,
                        ),
                    )
                    return UUID(str(row["id"]))
        except psycopg.errors.UniqueViolation:
            if place.kakao_place_id:
                cursor = await conn.execute(
                    "SELECT id FROM public.places WHERE kakao_place_id = %s OR natural_key = %s LIMIT 1",
                    (place.kakao_place_id, place.natural_key)
                )
                row = await cursor.fetchone()
                if row:
                    existing_id = UUID(str(row["id"]))
            else:
                cursor = await conn.execute(
                    "SELECT id FROM public.places WHERE natural_key = %s LIMIT 1",
                    (place.natural_key,)
                )
                row = await cursor.fetchone()
                if row:
                    existing_id = UUID(str(row["id"]))

            if existing_id:
                await conn.execute(
                    """
                    UPDATE public.places
                    SET
                      kakao_place_id = COALESCE(%s, kakao_place_id),
                      name = %s,
                      road_address = %s,
                      jibun_address = %s,
                      road_address_part = %s,
                      latitude = %s,
                      longitude = %s,
                      category = %s,
                      phone = %s,
                      valid_place = %s,
                      is_restaurant_like = %s,
                      is_chain = %s,
                      is_large_chain = %s,
                      chain_brand = %s,
                      chain_scale = %s,
                      updated_at = now()
                    WHERE id = %s
                    """,
                    (
                        place.kakao_place_id,
                        place.name,
                        place.road_address,
                        place.jibun_address,
                        place.road_address_part,
                        place.latitude,
                        place.longitude,
                        place.category,
                        place.phone,
                        place.valid_place,
                        place.is_restaurant_like,
                        place.is_chain,
                        place.is_large_chain,
                        place.chain_brand,
                        place.chain_scale,
                        existing_id,
                    )
                )
                return existing_id
            else:
                raise

    async def _upsert_visit(
        self,
        conn: psycopg.AsyncConnection[Any],
        *,
        visit: NormalizedVisit,
        place_id: UUID,
        source_id: UUID,
        extractor_model: str,
    ) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.place_visits (
              place_id, agency_id, source_id, visit_date, amount, party_size, purpose,
              department_name, rank_label, representative, payment_method, expense_category,
              raw_excerpt, extractor_model, extractor_confidence
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (agency_id, visit_date, place_id, amount, department_name) DO UPDATE SET
              source_id = EXCLUDED.source_id,
              party_size = EXCLUDED.party_size,
              purpose = EXCLUDED.purpose,
              rank_label = EXCLUDED.rank_label,
              representative = EXCLUDED.representative,
              payment_method = EXCLUDED.payment_method,
              expense_category = EXCLUDED.expense_category,
              raw_excerpt = EXCLUDED.raw_excerpt,
              extractor_model = EXCLUDED.extractor_model,
              extractor_confidence = EXCLUDED.extractor_confidence
            RETURNING id
            """,
            (
                place_id,
                visit.agency_id,
                source_id,
                visit.visit_date,
                visit.amount,
                visit.party_size,
                visit.purpose,
                visit.department_name,
                visit.rank_label,
                visit.representative,
                visit.payment_method,
                visit.expense_category,
                visit.raw_excerpt,
                extractor_model,
                visit.confidence,
            ),
        )
        return UUID(str(row["id"]))

    async def _fetch_one(
        self,
        conn: psycopg.AsyncConnection[Any],
        query: str,
        params: tuple[Any, ...],
    ) -> dict[str, Any]:
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Postgres query returned no row")
        return dict(row)


def apply_schema(*, database_url: str | None = None, migration_path: Path | None = None) -> None:
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise PipelineConfigError("DATABASE_URL is required for schema migration")
    path = migration_path or Path("supabase/migrations/20260523235106_initial.sql")
    sql = path.read_text(encoding="utf-8")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(sql)


def refresh_materialized_views(*, database_url: str | None = None) -> None:
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise PipelineConfigError("DATABASE_URL is required for refreshing materialized views")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY public.place_grade_v1")
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY public.agency_stats_v1")
