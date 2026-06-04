import os
import json
import time
import psycopg
import httpx
from pathlib import Path

def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "package.json").exists():
            return parent
    return Path.cwd()

def load_env():
    env_path = find_project_root() / ".env.local"
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip("'\"")
    return env_vars

def geocode_agency(client, headers, agency):
    name = agency["name"]
    parent = agency["parent_region"] or ""
    sub = agency["sub_region"] or ""
    
    # Try different queries in order of specificity
    queries = []
    queries.append(name)
    
    # If name doesn't contain sub-region or parent region, add it
    if sub and sub not in name:
        queries.append(f"{sub} {name}")
    if parent and parent not in name:
        queries.append(f"{parent} {name}")
    if parent and sub and parent not in name and sub not in name:
        queries.append(f"{parent} {sub} {name}")
        
    # For utility companies (상수도, 하수도, etc.)
    if "상수도" in name:
        queries.extend([
            name.replace("상수도", " 수도사업소"),
            name.replace("상수도", " 상하수도사업소"),
            name.replace("상수도", " 상수도사업소"),
            name.replace("상수도", " 수도과"),
            name.replace("상수도", " 상하수도과"),
        ])
    if "하수도" in name:
        queries.extend([
            name.replace("하수도", " 하수과"),
            name.replace("하수도", " 상하수도사업소"),
            name.replace("하수도", " 하수도과"),
            name.replace("하수도", " 상하수도과"),
        ])
        
    # If there's a sub_region or parent_region, we can append City Hall / County Office as last fallback
    if sub:
        if sub.endswith("구"):
            queries.append(f"{sub}청")
        elif sub.endswith("시"):
            queries.append(f"{sub}청")
        elif sub.endswith("군"):
            queries.append(f"{sub}군청")
    elif parent:
        if parent.endswith("시"):
            queries.append(f"{parent}청")
            
    # Also add a simplified fallback (e.g. "강남구의회" instead of "서울특별시 강남구의회")
    short_name = name
    for prefix in ["서울특별시 ", "경기도 ", "인천광역시 ", "부산광역시 ", "대구광역시 ", "대전광역시 ", "광주광역시 ", "울산광역시 ", "세종특별자치시 "]:
        if name.startswith(prefix):
            short_name = name.replace(prefix, "")
            if short_name not in queries:
                queries.append(short_name)
            break
            
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    for query in queries:
        try:
            response = client.get(url, params={"query": query, "size": 1}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                docs = data.get("documents", [])
                if docs:
                    doc = docs[0]
                    return {
                        "latitude": float(doc["y"]),
                        "longitude": float(doc["x"]),
                        "name": doc["place_name"],
                        "address": doc.get("road_address_name") or doc.get("address_name") or ""
                    }
        except Exception as e:
            print(f"Error querying Kakao API with query '{query}': {e}")
        time.sleep(0.05)
        
    return None

def main():
    env = load_env()
    db_url = env.get("DATABASE_URL") or os.getenv("DATABASE_URL")
    kakao_key = env.get("KAKAO_REST_KEY") or os.getenv("KAKAO_REST_KEY")
    
    if not db_url:
        raise ValueError("DATABASE_URL is not configured.")
    if not kakao_key:
        raise ValueError("KAKAO_REST_KEY is not configured.")

    print("Connecting to DB to fetch agencies...")
    agencies = []
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, parent_region, sub_region FROM agencies;")
            for row in cur.fetchall():
                agencies.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "parent_region": row[2],
                    "sub_region": row[3]
                })
                
    print(f"Fetched {len(agencies)} agencies.")
    
    output_path = Path(__file__).parent / "agency_coordinates.json"
    
    results = {}
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            print(f"Loaded {len(results)} existing geocoded records.")
        except Exception as e:
            print(f"Error loading existing coordinates file: {e}")
            
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    
    updated_count = 0
    failed_agencies = []
    
    with httpx.Client(timeout=15.0) as client:
        for idx, agency in enumerate(agencies, 1):
            agency_id = agency["id"]
            name = agency["name"]
            
            # If already geocoded and has lat/lng, skip
            if agency_id in results and results[agency_id].get("latitude") and results[agency_id].get("longitude"):
                continue
                
            # codeql[py/clear-text-logging-sensitive-data]
            print(f"[{idx}/{len(agencies)}] Geocoding: {name} ({agency_id})...")
            coord = geocode_agency(client, headers, agency)
            if coord:
                results[agency_id] = coord
                # codeql[py/clear-text-logging-sensitive-data]
                print(f"  Success: {coord['name']} -> ({coord['latitude']}, {coord['longitude']})")
                updated_count += 1
            else:
                # codeql[py/clear-text-logging-sensitive-data]
                print(f"  Failed: {name}")
                failed_agencies.append(agency)
                
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\nProcessing Complete.")
    print(f"Total agencies processed: {len(agencies)}")
    print(f"Geocoded successfully: {len(results)}")
    print(f"Newly geocoded: {updated_count}")
    print(f"Failed: {len(failed_agencies)}")
    if failed_agencies:
        print("Failed agencies list:")
        for fa in failed_agencies:
            # codeql[py/clear-text-logging-sensitive-data]
            print(f"  - {fa['name']} (ID: {fa['id']})")

if __name__ == "__main__":
    main()
