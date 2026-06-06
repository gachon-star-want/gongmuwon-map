#!/usr/bin/env python3
"""
Phase D: 전수 재처리 실행 스크립트
Phase B~C 변경사항을 기존 DB 데이터에 즉시 적용.

사용법:
  python3 reprocess_now.py --db-url "postgresql://..."

적용 내용:
  1. 체인 재검출 (classify_large_chain_brand 기반, API 호출 불필요)
  2. 지역 불일치 탐지 및 valid_place = FALSE 마킹
  3. 변경 내역 리포트 출력
"""

import argparse
import re
import sys
from collections import Counter

import psycopg2
from psycopg2.extras import execute_values

NON_REGION_PARENTS = frozenset({
    "문화체육관광부", "기후에너지환경부", "대통령실", "교육부", "행정안전부",
    "국토교통부", "산업통상자원부", "보건복지부", "고용노동부", "법무부",
    "기획재정부", "외교부", "과학기술정보통신부", "농림축산식품부", "중소벤처기업부",
    "해양수산부", "환경부", "통일부", "국방부", "여성가족부", "국가보훈부",
    "대한민국",
})

# Exact copy of classify_large_chain_brand from policy.py
_LARGE_CHAIN_BRANDS = (
    ("스타벅스", ("스타벅스", "starbucks")),
    ("투썸플레이스", ("투썸플레이스", "투썸", "twosome")),
    ("메가커피", ("메가커피", "메가mgc커피", "mega coffee", "megacoffee")),
    ("컴포즈커피", ("컴포즈커피", "컴포즈", "compose coffee", "composecoffee")),
    ("파리바게뜨", ("파리바게뜨", "파리바게트", "paris baguette", "parisbaguette")),
    ("뚜레쥬르", ("뚜레쥬르", "뚜레주르", "tous les jours", "touslesjours")),
    ("맥도날드", ("맥도날드", "mcdonald", "mcdonalds", "mcDonald's")),
    ("버거킹", ("버거킹", "burger king", "burgerking")),
    ("롯데리아", ("롯데리아", "lotteria")),
    ("써브웨이", ("써브웨이", "서브웨이", "subway")),
    ("이디야커피", ("이디야", "ediya")),
    ("빽다방", ("빽다방", "paik")),
    ("커피빈", ("커피빈", "coffee bean", "coffeebean")),
    ("할리스", ("할리스", "hollys")),
    ("배스킨라빈스", ("배스킨라빈스", "베스킨라빈스", "baskin")),
    ("던킨", ("던킨", "dunkin")),
    ("KFC", ("kfc",)),
    ("맘스터치", ("맘스터치", "mom's touch", "momstouch")),
    ("BBQ", ("bbq", "bbq치킨", "bbq chicken")),
    ("BHC", ("bhc", "bhc치킨", "bhc chicken")),
    ("교촌치킨", ("교촌", "kyochon")),
    ("네네치킨", ("네네치킨", "네네", "nene")),
    ("굽네치킨", ("굽네", "goobne")),
    ("페리카나", ("페리카나", "pelicana")),
    ("아웃백", ("아웃백", "outback", "outback steakhouse")),
    ("빕스", ("빕스", "vips")),
    ("애슐리", ("애슐리", "ashley")),
    ("도미노피자", ("도미노피자", "domino", "domino pizza")),
    ("피자헛", ("피자헛", "pizza hut", "pizzahut")),
    ("미스터피자", ("미스터피자", "mr pizza", "mrpizza")),
    ("본죽", ("본죽", "bonjuk")),
    ("김밥천국", ("김밥천국", "kimbap heaven")),
    ("한솥도시락", ("한솥도시락", "hansot")),
    ("파스쿠찌", ("파스쿠찌", "pasqucci")),
    ("엔제리너스", ("엔제리너스", "angel in us")),
    ("탐앤탐스", ("탐앤탐스", "tom n toms", "tomntoms")),
    ("노브랜드버거", ("노브랜드버거", "no brand burger")),
)

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


def _brand_key(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]+", "", value).lower()


def classify_large_chain_brand(value: str | None) -> str | None:
    if not value:
        return None
    key = _brand_key(value)
    for brand, aliases in _LARGE_CHAIN_BRANDS:
        if any(_brand_key(alias) in key for alias in aliases):
            return brand
    return None


def reclassify_chains(conn) -> dict:
    """Step 1: 체인 재검출"""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, is_large_chain, chain_brand
        FROM places
        WHERE deleted_at IS NULL
    """)
    rows = cur.fetchall()

    updates = []
    newly_flagged = 0
    already_flagged = 0
    brand_counts: Counter = Counter()

    for place_id, name, is_large_chain, chain_brand in rows:
        detected_brand = classify_large_chain_brand(name)
        if detected_brand:
            brand_counts[detected_brand] += 1
            updates.append((True, detected_brand, "대형전국체인", place_id))
            if not is_large_chain:
                newly_flagged += 1
            else:
                already_flagged += 1
        else:
            if is_large_chain and chain_brand:
                updates.append((False, None, None, place_id))

    # Batch update
    if updates:
        execute_values(cur, """
            UPDATE places AS p SET
                is_large_chain = v.is_large_chain::boolean,
                chain_brand = v.chain_brand::text,
                chain_scale = v.chain_scale::text
            FROM (VALUES %s) AS v(id, is_large_chain, chain_brand, chain_scale)
            WHERE p.id = v.id::uuid
        """, [(str(pid), flag, brand, scale) for flag, brand, scale, pid in updates],
                       template="(%s::uuid, %s::text, %s::text, %s::text)")
    conn.commit()

    return {
        "newly_flagged": newly_flagged,
        "already_flagged": already_flagged,
        "downgraded": len(updates) - newly_flagged - already_flagged,
        "brand_counts": brand_counts,
    }


def check_and_mark_region_mismatches(conn) -> dict:
    """Step 2: 지역 불일치 탐지 및 마킹"""
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.road_address_part,
               a.parent_region, COUNT(*) AS visit_count
        FROM place_visits pv
        JOIN places p ON p.id = pv.place_id
        JOIN agencies a ON a.id = pv.agency_id
        WHERE a.parent_region IS NOT NULL
          AND p.road_address_part IS NOT NULL
          AND p.is_large_chain = FALSE
        GROUP BY p.id, p.name, p.road_address_part, a.parent_region
        HAVING COUNT(*) > 0
        ORDER BY visit_count DESC
    """)
    rows = cur.fetchall()

    mismatched_place_ids = set()
    mismatched_by_region: Counter = Counter()
    mismatch_samples = []

    for place_id, name, road_address_part, parent_region, visit_count in rows:
        if parent_region in NON_REGION_PARENTS:
            continue
        agency_region = REGION_ALIASES.get(parent_region)
        place_prefix = road_address_part.split()[0] if road_address_part else ""
        place_region = REGION_ALIASES.get(place_prefix)
        if agency_region and place_region and agency_region != place_region:
            mismatched_place_ids.add(place_id)
            mismatched_by_region[f"{parent_region}→{road_address_part}"] += visit_count
            if len(mismatch_samples) < 20:
                mismatch_samples.append((name, parent_region, road_address_part, visit_count))

    # Mark mismatched places as needing reprocessing
    if mismatched_place_ids:
        place_ids_list = list(mismatched_place_ids)
        execute_values(cur, """
            UPDATE places AS p SET
                valid_place = FALSE
            FROM (VALUES %s) AS v(id)
            WHERE p.id = v.id::uuid
        """, [(str(pid),) for pid in place_ids_list], template="(%s::uuid)")
        conn.commit()

    return {
        "mismatch_count": len(mismatched_place_ids),
        "mismatched_by_region": mismatched_by_region,
        "samples": mismatch_samples,
    }


def print_report(chain_result: dict, region_result: dict) -> None:
    print("=" * 60)
    print("📋 REPROCESSING REPORT")
    print("=" * 60)

    print(f"\n1️⃣  CHAIN RECLASSIFICATION")
    print(f"   Newly flagged:    {chain_result['newly_flagged']}")
    print(f"   Already flagged:  {chain_result['already_flagged']}")
    print(f"   Downgraded:       {chain_result['downgraded']}")
    print(f"\n   Brand distribution (newly detected):")
    for brand, count in chain_result['brand_counts'].most_common():
        print(f"     {brand:20s} → {count}")

    print(f"\n2️⃣  REGION MISMATCH MARKED FOR REPROCESSING")
    print(f"   Mismatched places: {region_result['mismatch_count']}")
    if region_result['mismatch_count'] > 0:
        print(f"\n   Top mismatches:")
        for pair, count in region_result['mismatched_by_region'].most_common(10):
            print(f"     {pair:30s} → {count} visits")
        print(f"\n   Samples:")
        for name, a_region, p_region, visits in region_result['samples'][:10]:
            print(f"     {name:30s} | A={a_region:12s} P={p_region:12s} ({visits} visits)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full reprocessing for Phase B~C changes")
    parser.add_argument("--db-url", required=True, help="PostgreSQL connection URL")
    args = parser.parse_args()

    conn = psycopg2.connect(args.db_url)

    try:
        chain_result = reclassify_chains(conn)
        region_result = check_and_mark_region_mismatches(conn)
        print_report(chain_result, region_result)
    finally:
        conn.close()

    if region_result['mismatch_count'] > 0 or chain_result['newly_flagged'] > 0:
        print(f"\n{'=' * 60}")
        print("⚠️  Changes applied. Run the pipeline again to re-resolve mismatched places:")
        print("   uv run --project services/pipeline public-officer-pipeline run-agencies")
        print("   --scope nationwide --row-since 2024-01-01")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
