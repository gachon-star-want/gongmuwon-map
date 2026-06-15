"""거주적합도 POI 근거 ETL (ADR-019, P2b-POI).

data.go.kr odcloud OpenAPI에서 학교/어린이집 위치를 받아, shapely STRtree로
읍면동 경계 내(point-in-polygon) 카운트를 사전계산해 public.neighborhood_poi_counts에
적재한다. POI는 "근거 표시 전용" — 점수 MV에는 절대 들어가지 않는다(ADR-019).

- 학교/어린이집 표준데이터는 WGS84 경위도(변환 불필요).
- LocalData(welfare/convenience)는 EPSG:5174 → 4326 변환 필요(Phase 2, _transform_5174 준비).
- 좌표 결측·한국 bbox 밖은 스킵. 런타임 공간조인 금지(ADR-016, 오프라인 배치).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterator

import httpx
from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

ODCLOUD_BASE = "https://api.odcloud.kr/api"
# (lng_min, lat_min, lng_max, lat_max) — 한국 영역 좌표 sanity 필터
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)


@dataclass
class OdcloudDataset:
    """odcloud 표준데이터 1종 + POI 유형 매핑."""

    dataset_id: str
    uddi: str
    lat_field: str
    lng_field: str
    source_id: str
    type_field: str | None = None  # None이면 default_type 단일
    type_map: dict[str, str] = field(default_factory=dict)  # 원천 유형값 → poi_type
    default_type: str | None = None
    crs: str = "EPSG:4326"  # 표준데이터는 WGS84

    def poi_type_of(self, row: dict[str, Any]) -> str | None:
        if self.type_field is None:
            return self.default_type
        raw = str(row.get(self.type_field) or "").strip()
        return self.type_map.get(raw)


# Agent 검증으로 확정한 uddi/컬럼(키 승인 후 실응답으로 최종 확인)
SCHOOL = OdcloudDataset(
    dataset_id="15021148",
    uddi="uddi:67310bcf-928b-43cc-9833-eeb2f6c2886d",
    lat_field="위도",
    lng_field="경도",
    type_field="학교급구분",
    type_map={"초등학교": "elementary_school", "중학교": "middle_school", "고등학교": "high_school"},
    source_id="school_data",
)
CHILDCARE = OdcloudDataset(
    dataset_id="15013108",
    uddi="uddi:4cc38b42-9b9c-4665-a4c9-c313b2fb678c_202008311436",
    lat_field="위도",
    lng_field="경도",
    type_field=None,
    default_type="childcare",
    source_id="childcare_data",
)

EDUCATION_DATASETS = [SCHOOL, CHILDCARE]


class OdcloudClient:
    """odcloud 표준 페이징({data, totalCount, page})을 순회한다."""

    def __init__(self, service_key: str, *, timeout: float = 30.0, per_page: int = 1000) -> None:
        self._key = service_key
        self._per_page = per_page
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self) -> OdcloudClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def fetch_all(self, ds: OdcloudDataset) -> Iterator[dict[str, Any]]:
        page = 1
        seen = 0
        while True:
            resp = self._client.get(
                f"{ODCLOUD_BASE}/{ds.dataset_id}/v1/{ds.uddi}",
                params={"page": page, "perPage": self._per_page, "serviceKey": self._key, "returnType": "JSON"},
            )
            resp.raise_for_status()
            body = resp.json()
            rows = body.get("data") or []
            if not rows:
                break
            yield from rows
            seen += len(rows)
            total = body.get("totalCount") or 0
            if seen >= total or len(rows) < self._per_page:
                break
            page += 1


def _make_5174_to_4326():
    from pyproj import Transformer

    return Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)


def extract_points(ds: OdcloudDataset, rows: Iterator[dict[str, Any]]) -> list[tuple[str, float, float]]:
    """(poi_type, lng, lat) 리스트. 좌표 결측·한국 bbox 밖·미분류는 스킵."""
    out: list[tuple[str, float, float]] = []
    transformer = None if ds.crs == "EPSG:4326" else _make_5174_to_4326()
    lng_min, lat_min, lng_max, lat_max = KOREA_BBOX
    for row in rows:
        poi_type = ds.poi_type_of(row)
        if not poi_type:
            continue
        try:
            y = float(row[ds.lat_field])
            x = float(row[ds.lng_field])
        except (KeyError, TypeError, ValueError):
            continue
        if x == 0 or y == 0:
            continue
        if transformer is not None:
            # 5174는 (X=동거리, Y=북거리) → always_xy로 (x, y) 입력, (lng, lat) 출력
            lng, lat = transformer.transform(x, y)
        else:
            lat, lng = y, x
        if not (lng_min <= lng <= lng_max and lat_min <= lat <= lat_max):
            continue
        out.append((poi_type, lng, lat))
    return out


def load_emd_geometries(conn: Any) -> tuple[list[str], list[BaseGeometry]]:
    """region_boundaries(WGS84)에서 읍면동 경계를 로드. (adm_cd[], geom[]) 동일 인덱스."""
    cur = conn.execute(
        """SELECT b.adm_cd, b.geojson
           FROM public.region_boundaries b
           JOIN public.adm_regions r ON r.adm_cd = b.adm_cd AND r.level = 'emd'"""
    )
    adm_cds: list[str] = []
    geoms: list[BaseGeometry] = []
    for row in cur.fetchall():
        adm_cd = row[0] if not isinstance(row, dict) else row["adm_cd"]
        gj = row[1] if not isinstance(row, dict) else row["geojson"]
        if isinstance(gj, str):
            gj = json.loads(gj)
        geometry = gj.get("geometry", gj) if isinstance(gj, dict) else gj
        try:
            geom = shape(geometry)
        except Exception:
            continue
        if geom.is_empty:
            continue
        adm_cds.append(adm_cd)
        geoms.append(geom)
    return adm_cds, geoms


def count_pip(
    adm_cds: list[str],
    geoms: list[BaseGeometry],
    points: list[tuple[str, float, float]],
) -> dict[tuple[str, str], int]:
    """STRtree로 각 POI가 속한 읍면동을 찾아 (adm_cd, poi_type) 카운트."""
    if not geoms or not points:
        return {}
    tree = STRtree(geoms)
    counts: dict[tuple[str, str], int] = {}
    for poi_type, lng, lat in points:
        pt = Point(lng, lat)
        hits = tree.query(pt, predicate="contains")
        if len(hits) == 0:
            continue
        adm_cd = adm_cds[int(hits[0])]
        key = (adm_cd, poi_type)
        counts[key] = counts.get(key, 0) + 1
    return counts


def run_poi(
    *,
    database_url: str | None = None,
    service_key: str | None = None,
    datasets: list[OdcloudDataset] | None = None,
    ref_period: str = "2026",
    sido_filter: list[str] | None = None,
) -> dict[str, int]:
    """education POI를 받아 읍면동별 PIP 카운트를 적재. 반환: 요약 통계."""
    import psycopg
    from psycopg.types.json import Jsonb  # noqa: F401  (다른 적재와 일관성)

    url = database_url or os.getenv("DATABASE_URL")
    key = service_key or os.getenv("DATA_GO_KR_API_KEY")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    if not key:
        raise RuntimeError("DATA_GO_KR_API_KEY is required")
    datasets = datasets or EDUCATION_DATASETS

    with psycopg.connect(url, autocommit=True) as conn:
        adm_cds, geoms = load_emd_geometries(conn)
        if sido_filter:
            keep = {i for i, cd in enumerate(adm_cds) if cd[:2] in set(sido_filter)}
            adm_cds = [adm_cds[i] for i in keep]
            geoms = [geoms[i] for i in keep]

        # 적재 감사
        run = conn.execute(
            """INSERT INTO public.ingest_runs (source_id, scope, ref_period, status)
               VALUES ('data.go.kr-poi', %s, %s, 'running') RETURNING id""",
            (",".join(sido_filter) if sido_filter else "nationwide", ref_period),
        ).fetchone()
        run_id = run[0] if not isinstance(run, dict) else run["id"]

        total_points = 0
        all_counts: dict[tuple[str, str], int] = {}
        with OdcloudClient(key) as client:
            for ds in datasets:
                points = extract_points(ds, client.fetch_all(ds))
                total_points += len(points)
                for k, v in count_pip(adm_cds, geoms, points).items():
                    all_counts[k] = all_counts.get(k, 0) + v

        source_by_type = {}
        for ds in datasets:
            for t in {*ds.type_map.values(), ds.default_type}:
                if t:
                    source_by_type[t] = ds.source_id

        for (adm_cd, poi_type), cnt in all_counts.items():
            conn.execute(
                """INSERT INTO public.neighborhood_poi_counts
                       (adm_cd, poi_type, distance_basis, ref_period, count, source_id, ingest_run_id, updated_at)
                   VALUES (%s, %s, 'pip', %s, %s, %s, %s, now())
                   ON CONFLICT (adm_cd, poi_type, distance_basis, ref_period) DO UPDATE
                       SET count = EXCLUDED.count, source_id = EXCLUDED.source_id,
                           ingest_run_id = EXCLUDED.ingest_run_id, updated_at = now()""",
                (adm_cd, poi_type, ref_period, cnt, source_by_type.get(poi_type), run_id),
            )

        conn.execute(
            "UPDATE public.ingest_runs SET status='succeeded', finished_at=now(), row_count=%s WHERE id=%s",
            (len(all_counts), run_id),
        )

    return {"points": total_points, "rows": len(all_counts), "emd": len(adm_cds)}


__all__ = [
    "OdcloudDataset",
    "OdcloudClient",
    "SCHOOL",
    "CHILDCARE",
    "EDUCATION_DATASETS",
    "extract_points",
    "load_emd_geometries",
    "count_pip",
    "run_poi",
]
