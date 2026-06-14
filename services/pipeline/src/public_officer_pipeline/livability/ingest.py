from __future__ import annotations

import logging
import os
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from public_officer_pipeline.livability.kosis import KosisClient
from public_officer_pipeline.livability.sgis import SgisClient

logger = logging.getLogger(__name__)

# SGIS 통계주제도 지표: (metric_key, ctgr, stat_thema_map_id)
THEMAMAP_METRICS: list[tuple[str, str, str]] = [
    ("biz_per_1k", "CTGR_004", "M5DKMyEHJu20201130172257318wIEwIyKL8x"),
    ("childcare_access", "CTGR_003", "Mupzt7zwus20160121115806986Gn0IDrJIoz"),
    ("health_access", "CTGR_003", "H3Gn9rLznD20141030095228163Lo1DnuEFuL"),
    ("culture_access", "CTGR_003", "orJwxH8I6z20160121115806987yFL0ovrKrx"),
]
# SGIS population.json 필드 → metric_key
POPULATION_FIELDS: dict[str, str] = {
    "pop_density": "ppltn_dnsty",
    "avg_age": "avg_age",
    "aging_index": "aged_child_idx",
}
# KOSIS ITM_ID → 가구원수
KOSIS_ITM: dict[str, int] = {"T1": 1, "T2": 2, "T3": 3, "T4": 4, "T5": 5, "T8": 6}

SGIS_POP_YEAR = "2023"
SGIS_THEMA_YEAR = "2024"
SGIS_BOUNDARY_YEAR = "2023"
KOSIS_PERIOD = "2024"


def _num(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _make_transformer():
    from pyproj import Transformer

    return Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)


def _convert_ring(ring: list[Any], tf: Any) -> list[list[float]]:
    out: list[list[float]] = []
    for pt in ring:
        lng, lat = tf.transform(pt[0], pt[1])
        out.append([round(lng, 7), round(lat, 7)])
    return out


def _convert_geometry(geom: dict[str, Any], tf: Any) -> dict[str, Any]:
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        return {"type": gtype, "coordinates": [_convert_ring(r, tf) for r in coords]}
    if gtype == "MultiPolygon":
        return {"type": gtype, "coordinates": [[_convert_ring(r, tf) for r in poly] for poly in coords]}
    return geom


def _bbox_center(geom: dict[str, Any]) -> tuple[float | None, float | None, dict[str, float] | None]:
    xs: list[float] = []
    ys: list[float] = []

    def walk(node: Any) -> None:
        if isinstance(node, (list, tuple)) and node and isinstance(node[0], (int, float)):
            xs.append(node[0])
            ys.append(node[1])
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)

    walk(geom.get("coordinates"))
    if not xs:
        return None, None, None
    bbox = {"min_lng": min(xs), "min_lat": min(ys), "max_lng": max(xs), "max_lat": max(ys)}
    return (min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2, bbox


class LivabilityIngestor:
    def __init__(self, sgis: SgisClient, kosis: KosisClient, *, profile_version: int = 1) -> None:
        self.sgis = sgis
        self.kosis = kosis
        self.profile_version = profile_version
        self._kosis_cache: dict[str, dict[str, Any]] | None = None
        self._sido_names: dict[str, str] | None = None

    async def _sido_name(self, sido_cd: str) -> str:
        if self._sido_names is None:
            self._sido_names = {r["cd"]: r["addr_name"] for r in await self.sgis.stage()}
        return self._sido_names.get(sido_cd, sido_cd)

    async def _kosis_household(self) -> dict[str, dict[str, Any]]:
        if self._kosis_cache is None:
            rows = await self.kosis.household_by_size()
            indexed: dict[str, dict[str, Any]] = {}
            for row in rows:
                cd = row.get("C1")
                if cd:
                    indexed.setdefault(cd, {})[row.get("ITM_ID")] = row.get("DT")
            self._kosis_cache = indexed
        return self._kosis_cache

    async def ingest_sigungu(self, conn: psycopg.AsyncConnection[Any], sigungu_cd: str, run_id: Any) -> int:
        sido_cd = sigungu_cd[:2]
        sido_name = await self._sido_name(sido_cd)
        sigungu_lookup = {r["cd"]: r["addr_name"] for r in await self.sgis.stage(sido_cd)}
        sigungu_name = sigungu_lookup.get(sigungu_cd, sigungu_cd)
        emds = await self.sgis.stage(sigungu_cd)

        await self._upsert_region(conn, sido_cd, "sido", None, sido_name, sido_name)
        await self._upsert_region(
            conn, sigungu_cd, "sigungu", sido_cd, sigungu_name, f"{sido_name} {sigungu_name}"
        )

        # 경계(UTM-K) → WGS84 변환
        tf = _make_transformer()
        boundary = await self.sgis.boundary(sigungu_cd, SGIS_BOUNDARY_YEAR)
        geo_by_cd: dict[str, dict[str, Any]] = {}
        for feature in boundary.get("features", []) or []:
            props = feature.get("properties") or {}
            cd = props.get("adm_cd")
            geom = feature.get("geometry")
            if cd and geom:
                geo_by_cd[cd] = _convert_geometry(geom, tf)

        for emd in emds:
            cd = emd["cd"]
            name = emd["addr_name"]
            center_lat = center_lng = None
            bbox = None
            if cd in geo_by_cd:
                center_lat, center_lng, bbox = _bbox_center(geo_by_cd[cd])
            await self._upsert_region(
                conn, cd, "emd", sigungu_cd, name,
                f"{sido_name} {sigungu_name} {name}", center_lat, center_lng, bbox,
            )
            if cd in geo_by_cd:
                await conn.execute(
                    """
                    INSERT INTO public.region_boundaries (adm_cd, geojson, ref_year)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (adm_cd) DO UPDATE SET geojson = EXCLUDED.geojson, ref_year = EXCLUDED.ref_year
                    """,
                    (cd, Jsonb({"type": "Feature", "geometry": geo_by_cd[cd]}), int(SGIS_BOUNDARY_YEAR)),
                )

        # population 지표
        for row in await self.sgis.population(sigungu_cd, SGIS_POP_YEAR):
            cd = row.get("adm_cd")
            if not cd or len(cd) < 8:
                continue
            for metric_key, field in POPULATION_FIELDS.items():
                await self._metric(conn, cd, metric_key, 0, _num(row.get(field)), SGIS_POP_YEAR, run_id)

        # 통계주제도 지표
        for metric_key, ctgr, tid in THEMAMAP_METRICS:
            values = await self.sgis.themamap(ctgr, tid, sigungu_cd, SGIS_THEMA_YEAR)
            for cd, value in values.items():
                if len(cd) >= 8:
                    await self._metric(conn, cd, metric_key, 0, value, SGIS_THEMA_YEAR, run_id)

        # KOSIS 가구원수별 + 1인가구 비율
        kosis = await self._kosis_household()
        for emd in emds:
            cd = emd["cd"]
            row = kosis.get(cd)
            if not row:
                continue
            total = _num(row.get("T0"))
            one = _num(row.get("T1"))
            if total and one is not None:
                await self._metric(conn, cd, "solo_household_ratio", 0, round(one / total * 100, 1), KOSIS_PERIOD, run_id)
            for itm, size in KOSIS_ITM.items():
                value = _num(row.get(itm))
                if value is not None:
                    await self._metric(conn, cd, "household_count", size, value, KOSIS_PERIOD, run_id)

        return len(emds)

    async def _upsert_region(
        self,
        conn: psycopg.AsyncConnection[Any],
        adm_cd: str,
        level: str,
        parent_cd: str | None,
        name: str,
        full_name: str,
        center_lat: float | None = None,
        center_lng: float | None = None,
        bbox: dict[str, float] | None = None,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO public.adm_regions
              (adm_cd, level, parent_cd, name, full_name, center_lat, center_lng, bbox, ref_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (adm_cd) DO UPDATE SET
              level = EXCLUDED.level,
              parent_cd = EXCLUDED.parent_cd,
              name = EXCLUDED.name,
              full_name = EXCLUDED.full_name,
              center_lat = COALESCE(EXCLUDED.center_lat, public.adm_regions.center_lat),
              center_lng = COALESCE(EXCLUDED.center_lng, public.adm_regions.center_lng),
              bbox = COALESCE(EXCLUDED.bbox, public.adm_regions.bbox)
            """,
            (
                adm_cd, level, parent_cd, name, full_name, center_lat, center_lng,
                Jsonb(bbox) if bbox else None, 2024,
            ),
        )

    async def _metric(
        self,
        conn: psycopg.AsyncConnection[Any],
        adm_cd: str,
        metric_key: str,
        household_size: int,
        value: float | None,
        ref_period: str,
        run_id: Any,
    ) -> None:
        if value is None:
            return
        as_of = int(ref_period[:4]) if ref_period[:4].isdigit() else None
        await conn.execute(
            """
            INSERT INTO public.neighborhood_metrics
              (adm_cd, metric_key, household_size, value, ref_period, as_of_year, ingest_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (adm_cd, metric_key, household_size, ref_period) DO UPDATE SET
              value = EXCLUDED.value,
              as_of_year = EXCLUDED.as_of_year,
              ingest_run_id = EXCLUDED.ingest_run_id
            """,
            (adm_cd, metric_key, household_size, value, ref_period, as_of, run_id),
        )


async def run_livability(
    sigungu_cds: list[str],
    *,
    database_url: str | None = None,
    profile_version: int = 1,
) -> int:
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    sgis = SgisClient(os.getenv("SGIS_SERVICE_ID"), os.getenv("SGIS_API_KEY"))
    kosis = KosisClient(os.getenv("KOSIS_API_KEY"))
    ingestor = LivabilityIngestor(sgis, kosis, profile_version=profile_version)
    total = 0
    try:
        async with await psycopg.AsyncConnection.connect(url, autocommit=True, row_factory=dict_row) as conn:
            for sigungu_cd in sigungu_cds:
                cursor = await conn.execute(
                    """
                    INSERT INTO public.ingest_runs (source_id, scope, ref_period, status)
                    VALUES ('sgis+kosis', %s, %s, 'running') RETURNING id
                    """,
                    (sigungu_cd, KOSIS_PERIOD),
                )
                run_row = await cursor.fetchone()
                run_id = run_row["id"]
                try:
                    count = await ingestor.ingest_sigungu(conn, sigungu_cd, run_id)
                    await conn.execute(
                        "UPDATE public.ingest_runs SET status='success', row_count=%s, finished_at=now() WHERE id=%s",
                        (count, run_id),
                    )
                    total += count
                    logger.info("livability ingest %s: %d emd", sigungu_cd, count)
                except Exception:
                    await conn.execute(
                        "UPDATE public.ingest_runs SET status='error', finished_at=now() WHERE id=%s",
                        (run_id,),
                    )
                    raise
            await conn.execute("SELECT public.refresh_neighborhood_scores()")
    finally:
        await sgis.aclose()
        await kosis.aclose()
    return total
