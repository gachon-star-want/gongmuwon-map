#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { Pool } from 'pg';
import { roadAddressPart } from './_lib/address-utils.mjs';

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
  const args = process.argv.slice(2);
  const mode = args.includes('--mode=apply') ? 'apply' : 'dry-run';
  console.log(`Filling missing place coordinates in mode: ${mode}`);

  const env = { ...readDotEnv('.env.local'), ...process.env };
  const connectionString = env.DATABASE_URL;
  if (!connectionString) {
    throw new Error('DATABASE_URL is missing in .env.local');
  }

  // Load agency coordinates
  const coordsPath = path.join('services/pipeline/src/public_officer_pipeline/entity/agency_coordinates.json');
  if (!fs.existsSync(coordsPath)) {
    throw new Error('agency_coordinates.json not found. Run AgencyGeocodingAgent first.');
  }
  const agencyCoordinates = JSON.parse(fs.readFileSync(coordsPath, 'utf8'));

  const pool = new Pool({ connectionString, max: 1 });
  
  try {
    // Query places with missing coordinates and link them to the most frequent visiting agency
    console.log('Querying places with missing coordinates...');
    const result = await pool.query(`
      WITH place_agency AS (
        SELECT 
          v.place_id, 
          v.agency_id,
          count(*)::int as count,
          ROW_NUMBER() OVER (PARTITION BY v.place_id ORDER BY COUNT(*) DESC) as rn
        FROM public.place_visits v
        JOIN public.places p ON p.id = v.place_id
        WHERE p.latitude IS NULL OR p.longitude IS NULL
        GROUP BY v.place_id, v.agency_id
      )
      SELECT place_id, agency_id, count
      FROM place_agency
      WHERE rn = 1
    `);

    const missingPlaces = result.rows;
    console.log(`Found ${missingPlaces.length} places with missing coordinates.`);

    if (mode === 'apply') {
      const BATCH_SIZE = 500;
      let filledCount = 0;

      for (let i = 0; i < missingPlaces.length; i += BATCH_SIZE) {
        const batch = missingPlaces.slice(i, i + BATCH_SIZE);
        const data = [];
        
        for (const row of batch) {
          const agencyCoord = agencyCoordinates[row.agency_id];
          if (agencyCoord) {
            data.push({
              place_id: row.place_id,
              lat: agencyCoord.latitude,
              lng: agencyCoord.longitude,
              part: roadAddressPart(agencyCoord.address),
              address: agencyCoord.address
            });
          }
        }

        if (data.length > 0) {
          await pool.query(`
            UPDATE public.places AS p
            SET
              latitude = d.lat,
              longitude = d.lng,
              road_address_part = COALESCE(p.road_address_part, d.part),
              road_address = COALESCE(p.road_address, d.addr),
              updated_at = now()
            FROM (SELECT * FROM UNNEST($1::uuid[], $2::double precision[], $3::double precision[], $4::text[], $5::text[]) 
                  AS t(id, lat, lng, part, addr)) AS d
            WHERE p.id = d.id
          `, [
            data.map(d => d.place_id),
            data.map(d => d.lat),
            data.map(d => d.lng),
            data.map(d => d.part),
            data.map(d => d.address)
          ]);
          filledCount += data.length;
        }
        const processed = Math.min(i + BATCH_SIZE, missingPlaces.length);
        console.log(`Progress: ${processed} / ${missingPlaces.length} processed (${filledCount} updated).`);
      }

      console.log(`Successfully filled coordinates for ${filledCount} places.`);
      console.log('Refreshing database materialized views...');
      await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.place_grade_v1');
      await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.agency_stats_v1');
      console.log('Materialized views refreshed.');
    } else {
      // Dry-run preview
      console.log('Dry-run preview (first 10 items):');
      missingPlaces.slice(0, 10).forEach((row, idx) => {
        const { place_id, agency_id, count } = row;
        const agencyCoord = agencyCoordinates[agency_id];
        if (agencyCoord) {
          console.log(`${idx + 1}. Place ID: ${place_id} (Visited ${count} times) -> Agency: ${agencyCoord.name} (${agencyCoord.address})`);
        }
      });
      console.log('\nUse --mode=apply to apply these updates to the database.');
    }

  } catch (error) {
    console.error('Error occurred:', error);
    process.exitCode = 1;
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
