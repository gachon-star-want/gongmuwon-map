from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from public_officer_pipeline.models import Agency, NormalizedVisit, PipelineConfigError, ResolvedPlace


class PostgresLoader:
    def __init__(self, *, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise PipelineConfigError("DATABASE_URL is required for loading")

    async def load(
        self,
        *,
        agency: Agency,
        source_url: str,
        source_title: str,
        source_published_at: date | None,
        source_hash_sha256: str,
        resolved_places: dict[str, ResolvedPlace],
        visits: list[NormalizedVisit],
        storage_path: str | None = None,
    ) -> tuple[int, int, int]:
        async with await psycopg.AsyncConnection.connect(
            self.database_url,
            row_factory=dict_row,
        ) as conn:
            async with conn.transaction():
                await self._upsert_agency(conn, agency)
                source_id = await self._upsert_source(
                    conn,
                    agency=agency,
                    source_url=source_url,
                    source_title=source_title,
                    source_published_at=source_published_at,
                    source_hash_sha256=source_hash_sha256,
                    storage_path=storage_path,
                )

                place_ids: dict[str, UUID] = {}
                for place in resolved_places.values():
                    place_ids[place.natural_key] = await self._upsert_place(conn, place)

                visit_ids = []
                for visit in visits:
                    resolved = resolved_places[visit.place_raw.model_dump_json()]
                    visit_ids.append(
                        await self._upsert_visit(
                            conn,
                            visit=visit,
                            place_id=place_ids[resolved.natural_key],
                            source_id=source_id,
                        )
                    )

        return 1, len(place_ids), len(visit_ids)

    async def _upsert_agency(self, conn: psycopg.AsyncConnection[Any], agency: Agency) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.agencies (
              id, name, short_name, kind, parent_region, sub_region, homepage, source_pattern
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (kind, parent_region, sub_region) DO UPDATE SET
              name = EXCLUDED.name,
              short_name = EXCLUDED.short_name,
              homepage = EXCLUDED.homepage,
              source_pattern = EXCLUDED.source_pattern
            RETURNING id
            """,
            (
                agency.id,
                agency.name,
                agency.short_name,
                agency.kind.value,
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
        storage_path: str | None,
    ) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.sources (
              agency_id, url, title, published_at, file_kind, storage_path, hash_sha256
            )
            VALUES (%s, %s, %s, %s, 'html', %s, %s)
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
                storage_path,
                source_hash_sha256,
            ),
        )
        return UUID(str(row["id"]))

    async def _upsert_place(self, conn: psycopg.AsyncConnection[Any], place: ResolvedPlace) -> UUID:
        row = await self._fetch_one(
            conn,
            """
            INSERT INTO public.places (
              kakao_place_id, natural_key, name, road_address, jibun_address,
              road_address_part, latitude, longitude, category, phone
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            ),
        )
        return UUID(str(row["id"]))

    async def _upsert_visit(
        self,
        conn: psycopg.AsyncConnection[Any],
        *,
        visit: NormalizedVisit,
        place_id: UUID,
        source_id: UUID,
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
                "claude-haiku-4-5",
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
