"""동네 한 줄 요약 월배치 생성 (ADR-018, P2b-요약).

neighborhood_field_scores_v1(시군구 내 분야 percentile)를 읽어 동별로
강점/약점 claim을 도출하고, LLM 윤색(게이트 통과 시)을 거쳐 deterministic
폴백과 함께 public.neighborhood_summaries(household_size=0 공통)에 upsert한다.

요약의 강점/약점은 가구원수 무관(가중치 전 상대치)이라 동별 1건만 만든다.
LLM 키가 없거나 윤색 게이트 실패 시 룰 기반 요약으로 폴백하므로, 키 없이도
전체가 정상 동작한다.

실행: services/pipeline/.venv/bin/python services/pipeline/scripts/generate_neighborhood_summaries.py [--no-llm] [--limit N] [--sido 33 ...]
환경변수(DATABASE_URL, ANTHROPIC_API_KEY/GEMINI_API_KEY/OPENAI_API_KEY)는 .env.local에서 로드.
"""
from __future__ import annotations

import argparse
import asyncio
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


def _build_client(use_llm: bool):
    if not use_llm:
        return None
    keys = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }
    if not any(keys.values()):
        print("LLM 키 없음 → 룰 기반 요약으로만 생성", flush=True)
        return None
    from public_officer_pipeline.llm.client import LLMClient

    return LLMClient(**keys)


async def main() -> None:
    parser = argparse.ArgumentParser(description="동네 한 줄 요약 월배치 생성")
    parser.add_argument("--no-llm", action="store_true", help="LLM 윤색 없이 룰 기반만")
    parser.add_argument("--limit", type=int, default=0, help="동 개수 제한(테스트)")
    parser.add_argument("--sido", nargs="*", default=[], help="시도 코드 필터(예: 33)")
    args = parser.parse_args()

    _load_env()
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb

    from public_officer_pipeline.livability.summary import generate_summary

    url = os.environ["DATABASE_URL"]
    client = _build_client(use_llm=not args.no_llm)

    where = ["r.level = 'emd'"]
    params: list[object] = []
    if args.sido:
        where.append("left(r.adm_cd, 2) = ANY(%s)")
        params.append(args.sido)
    sql = f"""
        SELECT r.adm_cd, r.name AS region_name, p.name AS sigungu_name,
               f.category, f.field_score, f.rank_in_sigungu, f.sigungu_count
        FROM public.adm_regions r
        JOIN public.adm_regions p ON p.adm_cd = r.parent_cd
        JOIN public.neighborhood_field_scores_v1 f ON f.adm_cd = r.adm_cd
        WHERE {' AND '.join(where)}
        ORDER BY r.adm_cd
    """

    ok = rule = llm = 0
    async with await psycopg.AsyncConnection.connect(url, autocommit=True, row_factory=dict_row) as conn:
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()

        # 동별로 분야(fields)를 모은다
        by_emd: dict[str, dict[str, object]] = {}
        for row in rows:
            emd = by_emd.setdefault(
                row["adm_cd"],
                {"region_name": row["region_name"], "sigungu_name": row["sigungu_name"], "fields": []},
            )
            emd["fields"].append(
                {
                    "category": row["category"],
                    "rank": row["rank_in_sigungu"],
                    "total": row["sigungu_count"],
                    "percentile": float(row["field_score"]) if row["field_score"] is not None else 0.0,
                }
            )

        adm_cds = list(by_emd)
        if args.limit:
            adm_cds = adm_cds[: args.limit]
        print(f"요약 생성 대상 {len(adm_cds)}개 동 (LLM={'on' if client else 'off'})", flush=True)

        for i, adm_cd in enumerate(adm_cds, 1):
            emd = by_emd[adm_cd]
            result = await generate_summary(
                client=client,
                fields=emd["fields"],  # type: ignore[arg-type]
                region_name=str(emd["region_name"]),
                sigungu_name=str(emd["sigungu_name"]),
                household=0,
            )
            await conn.execute(
                """
                INSERT INTO public.neighborhood_summaries
                    (adm_cd, household_size, profile_version, summary, claims, source, model, generated_at)
                VALUES (%s, 0, 1, %s, %s, %s, %s, now())
                ON CONFLICT (adm_cd, household_size, profile_version) DO UPDATE
                    SET summary = EXCLUDED.summary, claims = EXCLUDED.claims,
                        source = EXCLUDED.source, model = EXCLUDED.model, generated_at = now()
                """,
                (adm_cd, result.summary, Jsonb(result.claims_json()), result.source, result.model),
            )
            ok += 1
            if result.source == "llm":
                llm += 1
            else:
                rule += 1
            if i % 100 == 0:
                print(f"  {i}/{len(adm_cds)} (llm={llm}, rule={rule})", flush=True)

    print(f"완료: {ok}개 (LLM 윤색 {llm}, 룰 폴백 {rule})", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
