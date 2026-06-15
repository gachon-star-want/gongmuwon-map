"""거주적합도 POI 근거 적재 실행 (ADR-019, P2b-POI).

data.go.kr odcloud에서 학교/어린이집 위치를 받아 읍면동 경계 내(PIP) 카운트를
public.neighborhood_poi_counts에 적재한다. POI는 점수와 무관(표시 전용).

실행: services/pipeline/.venv/bin/python services/pipeline/scripts/ingest_poi.py [--sido 33 ...] [--ref-period 2026]
환경변수(DATABASE_URL, DATA_GO_KR_API_KEY)는 .env.local에서 로드.
"""
from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="POI 근거(학교/어린이집) PIP 적재")
    parser.add_argument("--sido", nargs="*", default=[], help="시도 코드 필터(예: 33)")
    parser.add_argument("--ref-period", default="2026", help="기준연도 라벨")
    args = parser.parse_args()

    _load_env()
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL 필요", file=sys.stderr)
        sys.exit(2)
    if not os.getenv("DATA_GO_KR_API_KEY"):
        print("DATA_GO_KR_API_KEY 필요", file=sys.stderr)
        sys.exit(2)

    from public_officer_pipeline.livability.poi import run_poi

    stats = run_poi(sido_filter=args.sido or None, ref_period=args.ref_period)
    print(f"완료: POI {stats['points']}건 → 카운트행 {stats['rows']} (대상 읍면동 {stats['emd']})", flush=True)


if __name__ == "__main__":
    main()
