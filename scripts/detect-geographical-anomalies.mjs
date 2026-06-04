#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { Pool } from 'pg';

function readDotEnv(filePath) {
  if (!fs.existsSync(filePath)) return {};
  return fs.readFileSync(filePath, 'utf8').split(/\n/).reduce((env, line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return env;
    const match = trimmed.match(/^([A-Z0-9_]+)=(")?(.*?)\2$/);
    if (match) env[match[1]] = match[3];
    return env;
  }, {});
}

async function main() {
  const env = { ...readDotEnv('.env.local'), ...process.env };
  const connectionString = env.DATABASE_URL;
  if (!connectionString) {
    throw new Error('DATABASE_URL is missing in .env.local');
  }

  const pool = new Pool({ connectionString, max: 1 });
  console.log('Connecting to Neon DB...');
  
  try {
    await pool.query('BEGIN READ ONLY');
    await pool.query("SET LOCAL statement_timeout = '60s'");

    // 1. 전체 방문 횟수 및 고유 식당 수
    const totalCountRes = await pool.query(`
      SELECT 
        COUNT(*)::int as total_visits,
        COUNT(DISTINCT place_id)::int as total_places
      FROM public.place_visits
    `);
    const { total_visits, total_places } = totalCountRes.rows[0];
    console.log(`Total visits: ${total_visits}, Total unique places: ${total_places}`);

    // 2. 기관의 parent_region과 식당의 주소가 매칭되지 않는 건 찾기
    // 한국 행정구역 매핑용 단순 정규화 함수나 규칙 적용
    // 대전광역시 -> 대전, 서울특별시 -> 서울, 경기도 -> 경기, 인천광역시 -> 인천 등
    const anomalyRes = await pool.query(`
      WITH joined AS (
        SELECT 
          v.id as visit_id,
          v.visit_date,
          v.amount,
          v.department_name,
          a.name as agency_name,
          a.parent_region as agency_region,
          a.sub_region as agency_sub_region,
          p.id as place_id,
          p.name as place_name,
          p.road_address as place_road_address,
          p.jibun_address as place_jibun_address,
          p.road_address_part as place_road_address_part,
          p.kakao_place_id,
          p.natural_key,
          v.raw_excerpt
        FROM public.place_visits v
        JOIN public.agencies a ON v.agency_id = a.id
        JOIN public.places p ON v.place_id = p.id
        WHERE p.hidden_at IS NULL AND p.deleted_at IS NULL
      ),
      classified AS (
        SELECT 
          *,
          -- 기관 지역 축약어 (예: "서울특별시" -> "서울", "대전광역시" -> "대전")
          CASE 
            WHEN agency_region = '서울특별시' THEN '서울'
            WHEN agency_region = '대전광역시' THEN '대전'
            WHEN agency_region = '경기도' THEN '경기'
            WHEN agency_region = '인천광역시' THEN '인천'
            WHEN agency_region = '충청남도' THEN '충남'
            WHEN agency_region = '충청북도' THEN '충북'
            WHEN agency_region = '경상남도' THEN '경남'
            WHEN agency_region = '경상북도' THEN '경북'
            WHEN agency_region = '전라남도' THEN '전남'
            WHEN agency_region = '전라북도' THEN '전북'
            WHEN agency_region = '강원특별자치도' THEN '강원'
            WHEN agency_region = '제주특별자치도' THEN '제주'
            ELSE agency_region
          END as agency_region_short,
          
          -- 식당 지역 추출 (road_address 또는 jibun_address에서 첫 토큰)
          COALESCE(
            split_part(place_road_address, ' ', 1),
            split_part(place_jibun_address, ' ', 1),
            split_part(place_road_address_part, ' ', 1)
          ) as place_region_first_token
        FROM joined
      ),
      anomalies AS (
        SELECT *,
          CASE
            -- 서울특별시 기관인데 식당 주소에 '서울'이 없거나
            WHEN agency_region_short = '서울' AND place_road_address NOT LIKE '%서울%' AND place_jibun_address NOT LIKE '%서울%' THEN true
            -- 대전광역시 기관인데 식당 주소에 '대전'이 없거나
            WHEN agency_region_short = '대전' AND place_road_address NOT LIKE '%대전%' AND place_jibun_address NOT LIKE '%대전%' THEN true
            -- 경기도 기관인데 식당 주소에 '경기'가 없거나
            WHEN agency_region_short = '경기' AND place_road_address NOT LIKE '%경기%' AND place_jibun_address NOT LIKE '%경기%' THEN true
            -- 인천광역시 기관인데 식당 주소에 '인천'이 없거나
            WHEN agency_region_short = '인천' AND place_road_address NOT LIKE '%인천%' AND place_jibun_address NOT LIKE '%인천%' THEN true
            -- 그 외 지역에 대해서도 일치 검증
            WHEN agency_region_short NOT IN ('서울', '대전', '경기', '인천') AND 
                 place_road_address NOT LIKE '%' || agency_region_short || '%' AND 
                 place_jibun_address NOT LIKE '%' || agency_region_short || '%' THEN true
            ELSE false
          END as is_geographical_anomaly
        FROM classified
      )
      SELECT *
      FROM anomalies
      WHERE is_geographical_anomaly = true
      ORDER BY agency_name, place_name
    `);

    const anomalies = anomalyRes.rows;
    console.log(`Detected geographical anomalies: ${anomalies.length} visits`);

    // 3. 고유한 식당 기준으로 집계
    const uniqueAnomalyPlaces = {};
    for (const row of anomalies) {
      if (!uniqueAnomalyPlaces[row.place_id]) {
        uniqueAnomalyPlaces[row.place_id] = {
          place_id: row.place_id,
          place_name: row.place_name,
          place_address: row.place_road_address || row.place_jibun_address,
          kakao_place_id: row.kakao_place_id,
          natural_key: row.natural_key,
          agency_region: row.agency_region,
          agency_names: new Set(),
          visit_count: 0,
          raw_excerpts: []
        };
      }
      uniqueAnomalyPlaces[row.place_id].agency_names.add(row.agency_name);
      uniqueAnomalyPlaces[row.place_id].visit_count += 1;
      if (row.raw_excerpt && uniqueAnomalyPlaces[row.place_id].raw_excerpts.length < 3) {
        uniqueAnomalyPlaces[row.place_id].raw_excerpts.push(row.raw_excerpt);
      }
    }

    const anomalyPlacesList = Object.values(uniqueAnomalyPlaces).map(p => ({
      ...p,
      agency_names: Array.from(p.agency_names)
    })).sort((a, b) => b.visit_count - a.visit_count);

    console.log(`Total unique anomaly places: ${anomalyPlacesList.length}`);

    const outputDir = process.argv[2] || '.';
    // 결과를 JSON 파일로 쓰기
    fs.writeFileSync(path.join(outputDir, 'anomaly_visits.json'), JSON.stringify(anomalies, null, 2), 'utf8');
    fs.writeFileSync(path.join(outputDir, 'anomaly_places.json'), JSON.stringify(anomalyPlacesList, null, 2), 'utf8');
    
    // 간략 리포트 출력
    console.log('\nTop 20 Geographical Anomalies (by Unique Place):');
    anomalyPlacesList.slice(0, 20).forEach((p, idx) => {
      console.log(`${idx + 1}. [${p.place_name}] (${p.place_address})`);
      console.log(`   - Agency Region: ${p.agency_region} (Visited by: ${p.agency_names.join(', ')})`);
      console.log(`   - Visits count: ${p.visit_count}, Kakao ID: ${p.kakao_place_id || 'None'}`);
      console.log(`   - Raw Excerpts: ${p.raw_excerpts.map(e => `"${e}"`).join(', ')}`);
    });

    await pool.query('ROLLBACK');
  } catch (error) {
    await pool.query('ROLLBACK').catch(() => {});
    throw error;
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
