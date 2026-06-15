"""전국 시군구 거주적합도 일괄 적재.

한 시군구 실패는 격리하고 계속한다(세종 등 특이 구조 대비). KOSIS 가구원수별
데이터는 LivabilityIngestor 캐시로 1회만 받아 공유한다. 마지막에 점수 MV refresh.

실행: services/pipeline/.venv/bin/python services/pipeline/scripts/ingest_nationwide_livability.py
환경변수(DATABASE_URL, SGIS_SERVICE_ID, SGIS_API_KEY, KOSIS_API_KEY)는 .env.local에서 로드한다.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load_env() -> None:
    env_path = ROOT / ".env.local"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[7:]
        key, value = s.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        os.environ.setdefault(key, value)


async def main() -> None:
    _load_env()
    import psycopg
    from psycopg.rows import dict_row

    from public_officer_pipeline.livability.ingest import LivabilityIngestor
    from public_officer_pipeline.livability.kosis import KosisClient
    from public_officer_pipeline.livability.sgis import SgisClient

    url = os.environ["DATABASE_URL"]
    sgis = SgisClient(os.getenv("SGIS_SERVICE_ID"), os.getenv("SGIS_API_KEY"))
    kosis = KosisClient(os.getenv("KOSIS_API_KEY"))
    ingestor = LivabilityIngestor(sgis, kosis)

    ok = fail = emd_total = 0
    try:
        sido_filters = sys.argv[1:]
        sidos = await sgis.stage()
        if sido_filters:
            sidos = [s for s in sidos if s["cd"] in sido_filters]
        sigungu: list[str] = []
        for sido in sidos:
            for sg in await sgis.stage(sido["cd"]):
                sigungu.append(sg["cd"])
        scope_label = f"시도 {','.join(sido_filters)}" if sido_filters else "전국"
        print(f"{scope_label} 시군구 {len(sigungu)}개 적재 시작", flush=True)

        async with await psycopg.AsyncConnection.connect(url, autocommit=True, row_factory=dict_row) as conn:
            for index, cd in enumerate(sigungu, 1):
                cursor = await conn.execute(
                    """INSERT INTO public.ingest_runs (source_id, scope, ref_period, status)
                       VALUES ('sgis+kosis', %s, '2024', 'running') RETURNING id""",
                    (cd,),
                )
                run_id = (await cursor.fetchone())["id"]
                try:
                    count = await ingestor.ingest_sigungu(conn, cd, run_id)
                    await conn.execute(
                        "UPDATE public.ingest_runs SET status='success', row_count=%s, finished_at=now() WHERE id=%s",
                        (count, run_id),
                    )
                    ok += 1
                    emd_total += count
                    print(f"[{index}/{len(sigungu)}] {cd} ✅ {count} emd", flush=True)
                except Exception as exc:  # noqa: BLE001 - 시군구 격리
                    await conn.execute(
                        "UPDATE public.ingest_runs SET status='error', finished_at=now() WHERE id=%s",
                        (run_id,),
                    )
                    fail += 1
                    print(f"[{index}/{len(sigungu)}] {cd} ❌ {str(exc)[:100]}", flush=True)
            print("점수 MV refresh...", flush=True)
            await conn.execute("SELECT public.refresh_neighborhood_scores()")
    finally:
        await sgis.aclose()
        await kosis.aclose()

    print(f"\n완료: 성공 {ok} 시군구, 실패 {fail}, 적재 읍면동 {emd_total}개", flush=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
