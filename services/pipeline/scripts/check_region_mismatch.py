#!/usr/bin/env python3
"""
CI 방어막: 파이프라인 완료 후 지역 불일치 건수를 확인한다.
0건이면 OK, 0건 이상이면 경고 메시지를 출력한다.

Usage:
  python3 check_region_mismatch.py --db-url "postgresql://..."
"""

import argparse
import sys

import psycopg2

NON_REGION_PARENTS = frozenset({
    "문화체육관광부", "기후에너지환경부", "대통령실", "교육부", "행정안전부",
    "국토교통부", "산업통상자원부", "보건복지부", "고용노동부", "법무부",
    "기획재정부", "외교부", "과학기술정보통신부", "농림축산식품부", "중소벤처기업부",
    "해양수산부", "환경부", "통일부", "국방부", "여성가족부", "국가보훈부",
    "대한민국",
})

REGION_ALIASES = {
    "서울": "서울특별시", "서울특별시": "서울특별시",
    "부산": "부산광역시", "부산광역시": "부산광역시",
    "대구": "대구광역시", "대구광역시": "대구광역시",
    "인천": "인천광역시", "인천광역시": "인천광역시",
    "광주": "광주광역시", "광주광역시": "광주광역시",
    "대전": "대전광역시", "대전광역시": "대전광역시",
    "울산": "울산광역시", "울산광역시": "울산광역시",
    "세종": "세종특별자치시", "세종특별자치시": "세종특별자치시",
    "경기": "경기도", "경기도": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도",
    "전북": "전라북도", "전라북도": "전라북도", "전북특별자치도": "전라북도",
    "전남": "전라남도", "전라남도": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도",
    "제주": "제주특별자치도", "제주특별자치도": "제주특별자치도",
}


def check_region_mismatch(db_url: str) -> int:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("""
        SELECT a.parent_region, p.road_address_part, COUNT(*) AS cnt
        FROM place_visits pv
        JOIN agencies a ON a.id = pv.agency_id
        JOIN places p ON p.id = pv.place_id
        WHERE a.parent_region IS NOT NULL
          AND p.road_address_part IS NOT NULL
        GROUP BY a.parent_region, p.road_address_part
        ORDER BY cnt DESC
    """)

    total_mismatches = 0
    mismatch_details = []

    for agency_region, place_region_part, count in cur.fetchall():
        if agency_region in NON_REGION_PARENTS:
            continue

        agency_short = REGION_ALIASES.get(agency_region)
        place_prefix = place_region_part.split()[0] if place_region_part else ""
        place_short = REGION_ALIASES.get(place_prefix)

        if agency_short and place_short and agency_short != place_short:
            total_mismatches += count
            mismatch_details.append((agency_region, place_region_part, count))

    cur.close()
    conn.close()

    if total_mismatches == 0:
        print(f"  ✅ Region mismatch check: {total_mismatches} (clean)")
        return 0

    print(f"  ⚠️  Region mismatch check: {total_mismatches}")
    print("  Top mismatches:")
    for agency_region, place_region_part, count in mismatch_details[:10]:
        print(f"    {agency_region:15s} → {place_region_part:20s} ({count} visits)")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check region mismatches between agency and resolved place"
    )
    parser.add_argument("--db-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument("--fail-on-mismatch", action="store_true",
                        help="Exit with code 1 if mismatches found")
    args = parser.parse_args()

    exit_code = check_region_mismatch(args.db_url)
    if args.fail_on_mismatch:
        sys.exit(exit_code)
    sys.exit(0)


if __name__ == "__main__":
    main()
