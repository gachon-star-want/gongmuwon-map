#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import { Pool } from 'pg';

const KAKAO_KEYWORD_URL = 'https://dapi.kakao.com/v2/local/search/keyword.json';
const BASE32 = '0123456789bcdefghjkmnpqrstuvwxyz';

// Utility: Geohash Encoder (7 precision)
function encodeGeohash(latitude, longitude, precision = 7) {
  let latMin = -90, latMax = 90;
  let lonMin = -180, lonMax = 180;
  let geohash = '';
  let isEven = true;
  let bit = 0;
  let ch = 0;

  while (geohash.length < precision) {
    let mid;
    if (isEven) {
      mid = (lonMin + lonMax) / 2;
      if (longitude > mid) {
        ch |= (1 << (4 - bit));
        lonMin = mid;
      } else {
        lonMax = mid;
      }
    } else {
      mid = (latMin + latMax) / 2;
      if (latitude > mid) {
        ch |= (1 << (4 - bit));
        latMin = mid;
      } else {
        latMax = mid;
      }
    }

    isEven = !isEven;
    if (bit < 4) {
      bit += 1;
    } else {
      geohash += BASE32[ch];
      bit = 0;
      ch = 0;
    }
  }
  return geohash;
}

// Utility: Name normalization
function normalizeName(value) {
  return value.replace(/[\s㈜주식회사()（）·.,-]+/g, '').toLowerCase();
}

// Utility: Address normalization
function normalizeAddress(value) {
  if (!value) return '';
  return value.replace(/[\s·.,-]/g, '');
}

// Utility: Natural key SHA1 hash
function getNaturalKey(name, address, latitude, longitude) {
  const normName = normalizeName(name);
  let locationKey;
  if (latitude != null && longitude != null) {
    locationKey = encodeGeohash(Number(latitude), Number(longitude), 7);
  } else {
    locationKey = normalizeAddress(address);
  }
  const base = `${normName}|${locationKey}`;
  return crypto.createHash('sha1').update(base).digest('hex');
}

// Utility: Haversine distance
function haversineMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

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

async function searchKakao(query, lat, lon, apiKey) {
  const url = new URL(KAKAO_KEYWORD_URL);
  url.searchParams.set('query', query);
  url.searchParams.set('size', '5');
  url.searchParams.set('x', String(lon));
  url.searchParams.set('y', String(lat));
  url.searchParams.set('radius', '20000'); // 20km radius limit

  try {
    const res = await fetch(url, {
      headers: { Authorization: `KakaoAK ${apiKey}` }
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.documents || [];
  } catch (err) {
    console.error(`Kakao search failed for query: ${query}, error: ${err.message}`);
    return [];
  }
}

async function searchKakaoNoRadius(query, apiKey) {
  const url = new URL(KAKAO_KEYWORD_URL);
  url.searchParams.set('query', query);
  url.searchParams.set('size', '5');

  try {
    const res = await fetch(url, {
      headers: { Authorization: `KakaoAK ${apiKey}` }
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.documents || [];
  } catch (err) {
    return [];
  }
}

function roadAddressPart(address) {
  if (!address) return null;
  const match = address.match(/(서울(?:특별시)?|인천(?:광역시)?|대전(?:광역시)?|대구(?:광역시)?|광주(?:광역시)?|울산(?:광역시)?|부산(?:광역시)?|세종(?:특별자치시)?|경기(?:도)?|강원(?:특별자치도)?|충북|충남|전북|전남|경북|경남|제주(?:특별자치도)?)\s+([가-힣]+[구군시])/);
  if (match) {
    let region = match[1];
    if (region.startsWith('서울')) region = '서울';
    else if (region.startsWith('경기')) region = '경기';
    else if (region.startsWith('대전')) region = '대전';
    else if (region.startsWith('인천')) region = '인천';
    else if (region.startsWith('대구')) region = '대구';
    else if (region.startsWith('광주')) region = '광주';
    else if (region.startsWith('울산')) region = '울산';
    else if (region.startsWith('부산')) region = '부산';
    else if (region.startsWith('세종')) region = '세종';
    else if (region.startsWith('강원')) region = '강원';
    else if (region.startsWith('제주')) region = '제주';
    return `${region} ${match[2]}`;
  }
  return null;
}

// Check large chain brand
const LARGE_CHAINS = ['스타벅스', '투썸플레이스', '메가커피', '컴포즈커피', '파리바게뜨', '맥도날드', '버거킹', '롯데리아', '써브웨이', '이디야커피', '빽다방', '커피빈', '할리스', '배스킨라빈스', '던킨', 'KFC', '맘스터치'];
function isLargeChain(name) {
  const normalized = normalizeName(name);
  return LARGE_CHAINS.some(brand => normalizeName(brand).includes(normalized) || normalized.includes(normalizeName(brand)));
}

async function updatePlaceVisits(pool, targetPlaceId, visitIds) {
  for (const visitId of visitIds) {
    try {
      await pool.query(`
        UPDATE public.place_visits
        SET place_id = $1
        WHERE id = $2
      `, [targetPlaceId, visitId]);
    } catch (err) {
      if (err.code === '23505') {
        // Unique constraint violation: visit already exists under correct place_id
        await pool.query(`DELETE FROM public.place_visits WHERE id = $1`, [visitId]);
        console.log(`      (Deleted duplicate visit ID: ${visitId} due to unique constraint conflict)`);
      } else {
        throw err;
      }
    }
  }
}

async function main() {
  const args = process.argv.slice(2);
  const mode = args.includes('--mode=apply') ? 'apply' : 'dry-run';
  const limit = args.find(a => a.startsWith('--limit=')) ? Number(args.find(a => a.startsWith('--limit=')).split('=')[1]) : null;

  console.log(`Starting Geographical Anomaly Remediation in Mode: ${mode}`);

  const env = { ...readDotEnv('.env.local'), ...process.env };
  const connectionString = env.DATABASE_URL;
  const kakaoApiKey = env.KAKAO_REST_KEY;

  if (!connectionString) {
    throw new Error('DATABASE_URL is missing in .env.local');
  }
  if (!kakaoApiKey) {
    throw new Error('KAKAO_REST_KEY is missing in .env.local');
  }

  // Load agency coordinates
  const coordsPath = path.join('services/pipeline/src/public_officer_pipeline/entity/agency_coordinates.json');
  if (!fs.existsSync(coordsPath)) {
    throw new Error(`agency_coordinates.json not found at ${coordsPath}. Run AgencyGeocodingAgent first.`);
  }
  const agencyCoordinates = JSON.parse(fs.readFileSync(coordsPath, 'utf8'));

  const pool = new Pool({ connectionString, max: 1 });
  
  try {
    // 1. Fetch geographical anomaly groups (agency_id, place_id, place_name)
    console.log('Fetching geographical anomaly candidates from Neon DB...');
    const candidatesRes = await pool.query(`
      WITH joined AS (
        SELECT 
          v.id as visit_id,
          a.id as agency_id,
          a.name as agency_name,
          a.parent_region as agency_region,
          a.gov_tier,
          p.id as place_id,
          p.name as place_name,
          p.road_address as place_road_address,
          p.jibun_address as place_jibun_address,
          p.road_address_part as place_road_address_part
        FROM public.place_visits v
        JOIN public.agencies a ON v.agency_id = a.id
        JOIN public.places p ON v.place_id = p.id
        WHERE p.hidden_at IS NULL AND p.deleted_at IS NULL
      ),
      classified AS (
        SELECT 
          *,
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
          END as agency_region_short
        FROM joined
      ),
      anomalies AS (
        SELECT *,
          CASE
            WHEN agency_region_short = '서울' AND place_road_address NOT LIKE '%서울%' AND place_jibun_address NOT LIKE '%서울%' THEN true
            WHEN agency_region_short = '대전' AND place_road_address NOT LIKE '%대전%' AND place_jibun_address NOT LIKE '%대전%' THEN true
            WHEN agency_region_short = '경기' AND place_road_address NOT LIKE '%경기%' AND place_jibun_address NOT LIKE '%경기%' THEN true
            WHEN agency_region_short = '인천' AND place_road_address NOT LIKE '%인천%' AND place_jibun_address NOT LIKE '%인천%' THEN true
            WHEN agency_region_short NOT IN ('서울', '대전', '경기', '인천') AND 
                 place_road_address NOT LIKE '%' || agency_region_short || '%' AND 
                 place_jibun_address NOT LIKE '%' || agency_region_short || '%' THEN true
            ELSE false
          END as is_geographical_anomaly
        FROM classified
      )
      SELECT 
        agency_id, 
        agency_name, 
        agency_region,
        gov_tier,
        place_id, 
        place_name, 
        place_road_address,
        count(*)::int as visits_count,
        array_agg(visit_id::text) as visit_ids
      FROM anomalies
      WHERE is_geographical_anomaly = true
      GROUP BY agency_id, agency_name, agency_region, gov_tier, place_id, place_name, place_road_address
      ORDER BY visits_count DESC
    `);

    let rows = candidatesRes.rows;
    console.log(`Found ${rows.length} anomalous agency-place match groups.`);
    if (limit) {
      rows = rows.slice(0, limit);
      console.log(`Limiting execution to first ${limit} groups.`);
    }

    let processedCount = 0;
    let resolvedCount = 0;
    let fallbackCount = 0;

    for (const group of rows) {
      processedCount++;
      const { agency_id, agency_name, gov_tier, place_id, place_name, place_road_address, visits_count, visit_ids } = group;
      
      const agencyCoord = agencyCoordinates[agency_id];
      if (!agencyCoord) {
        console.warn(`[Skip] Agency coord missing for ${agency_name} (${agency_id})`);
        continue;
      }
      const { latitude: agencyLat, longitude: agencyLng } = agencyCoord;

      console.log(`[${processedCount}/${rows.length}] Resolving: ${place_name} for ${agency_name} (visits: ${visits_count})`);

      // 2. Perform localized Kakao Search
      let documents = await searchKakao(place_name, agencyLat, agencyLng, kakaoApiKey);
      
      // Kakao search delay
      await new Promise(r => setTimeout(r, 100));

      let matchedDoc = null;

      // Filter and validate candidates
      if (documents.length > 0) {
        for (const doc of documents) {
          const docLat = Number(doc.y);
          const docLng = Number(doc.x);
          const dist = haversineMeters(agencyLat, agencyLng, docLat, docLng);

          // Name validation: normalized names match or overlap
          const nameMatch = normalizeName(doc.place_name).includes(normalizeName(place_name)) || 
                            normalizeName(place_name).includes(normalizeName(doc.place_name));

          const distOk = dist <= 50000 || gov_tier === 'national' || gov_tier === 'constitutional' || isLargeChain(doc.place_name);

          if (nameMatch && distOk) {
            matchedDoc = doc;
            break;
          }
        }
      }

      if (mode === 'dry-run') {
        if (matchedDoc) {
          console.log(`   -> [Matched] Localized place found: ${matchedDoc.place_name} (${matchedDoc.road_address_name || matchedDoc.address_name}), dist: ${Math.round(haversineMeters(agencyLat, agencyLng, Number(matchedDoc.y), Number(matchedDoc.x)))}m`);
        } else {
          console.log(`   -> [Fallback] No local match found. Will disconnect from 성남 and create fallback place for ${agency_name}.`);
        }
        continue;
      }

      // mode === 'apply'
      if (matchedDoc) {
        const kakaoId = matchedDoc.id;
        const placeName = matchedDoc.place_name;
        const roadAddr = matchedDoc.road_address_name || null;
        const jibunAddr = matchedDoc.address_name || null;
        const lat = Number(matchedDoc.y);
        const lng = Number(matchedDoc.x);
        const cat = matchedDoc.category_name || null;
        const ph = matchedDoc.phone || null;
        const chainBrand = isLargeChain(placeName) ? placeName : null;

        // Check if correct place already exists in DB
        let checkRes = await pool.query(`SELECT id FROM public.places WHERE kakao_place_id = $1`, [kakaoId]);
        let targetPlaceId;

        if (checkRes.rows.length > 0) {
          targetPlaceId = checkRes.rows[0].id;
        } else {
          const newNatKey = getNaturalKey(placeName, roadAddr || jibunAddr, lat, lng);
          let checkNatKeyRes = await pool.query(`SELECT id FROM public.places WHERE natural_key = $1`, [newNatKey]);
          
          if (checkNatKeyRes.rows.length > 0) {
            targetPlaceId = checkNatKeyRes.rows[0].id;
            // Existing place with same natural_key - populate the kakao_place_id
            await pool.query(`
              UPDATE public.places 
              SET kakao_place_id = $1, updated_at = now() 
              WHERE id = $2
            `, [kakaoId, targetPlaceId]);
          } else {
            // Insert new place
            const insertRes = await pool.query(`
              INSERT INTO public.places (
                kakao_place_id, natural_key, name, road_address, jibun_address, 
                road_address_part, latitude, longitude, category, phone,
                is_chain, is_large_chain, chain_brand, chain_scale, updated_at
              ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, now()
              ) RETURNING id
            `, [
              kakaoId, newNatKey, placeName, roadAddr, jibunAddr, 
              roadAddressPart(roadAddr || jibunAddr), lat, lng, cat, ph,
              chainBrand !== null, chainBrand !== null, chainBrand, chainBrand ? '대형전국체인' : null
            ]);
            targetPlaceId = insertRes.rows[0].id;
          }
        }

        // Update visits to the correct place
        await updatePlaceVisits(pool, targetPlaceId, visit_ids);

        resolvedCount++;
        console.log(`   -> [SUCCESS] Relocated visits to place_id: ${targetPlaceId} (${placeName})`);
      } else {
        // Create fallback place mapping to local key to disconnect from incorrect place
        const fallbackName = place_name;
        const fallbackAddr = agencyCoord.address || `${agency_name} 인근`;
        const newNatKey = getNaturalKey(fallbackName, fallbackAddr, agencyLat, agencyLng);

        // Check if exists
        let checkRes = await pool.query(`SELECT id FROM public.places WHERE natural_key = $1`, [newNatKey]);
        let targetPlaceId;

        if (checkRes.rows.length > 0) {
          targetPlaceId = checkRes.rows[0].id;
        } else {
          // Insert fallback place
          const insertRes = await pool.query(`
            INSERT INTO public.places (
              kakao_place_id, natural_key, name, road_address, 
              road_address_part, latitude, longitude, updated_at
            ) VALUES (
              $1, $2, $3, $4, $5, $6, $7, now()
            ) RETURNING id
          `, [
            null, newNatKey, fallbackName, fallbackAddr,
            roadAddressPart(fallbackAddr), agencyLat, agencyLng
          ]);
          targetPlaceId = insertRes.rows[0].id;
        }

        // Update visits to the fallback place
        await updatePlaceVisits(pool, targetPlaceId, visit_ids);

        fallbackCount++;
        console.log(`   -> [FALLBACK] Isolated visits to fallback place_id: ${targetPlaceId} (${fallbackName})`);
      }
    }

    if (mode === 'apply') {
      console.log('Remediation database updates completed.');
      console.log(`Relocated Match Groups: ${resolvedCount}`);
      console.log(`Fallback Isolated Groups: ${fallbackCount}`);

      // Cleanup orphaned places (places with no visits left, which were incorrectly matched previously)
      console.log('Cleaning up orphaned places with 0 visits...');
      const cleanupRes = await pool.query(`
        WITH orphaned AS (
          SELECT p.id 
          FROM public.places p
          LEFT JOIN public.place_visits v ON v.place_id = p.id
          WHERE v.id IS NULL
        )
        DELETE FROM public.places
        WHERE id IN (SELECT id FROM orphaned)
      `);
      console.log(`Cleaned up ${cleanupRes.rowCount} orphaned places.`);

      // Refresh Materialized Views
      console.log('Refreshing database materialized views...');
      await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.place_grade_v1');
      await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.agency_stats_v1');
      console.log('Materialized views refreshed.');
    }

  } catch (error) {
    console.error('An error occurred during remediation:', error);
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
