#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { Pool } from 'pg';

const KAKAO_KEYWORD_URL = 'https://dapi.kakao.com/v2/local/search/keyword.json';
const DEFAULT_OUTPUT_ROOT = '/private/tmp/public-officer-marker-audit';
const DEFAULT_CACHE_DIR = '/private/tmp/public-officer-marker-audit-cache';
const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외 지자체·의회 공식 공개자료';

function usage() {
  return `Usage: node scripts/audit-markers.mjs [options]

Audits every visible map marker back to its place, visits, sources, and Kakao location evidence.
The DB transaction is forced READ ONLY.

Options:
  --target=service|readonly      service uses DATABASE_URL, readonly uses DATABASE_URL_READONLY (default: service)
  --env-file=.env.local          dotenv file to load without printing secrets
  --output-dir=path              output directory (default: timestamp under ${DEFAULT_OUTPUT_ROOT})
  --cache-dir=path               Kakao/source URL cache directory (default: ${DEFAULT_CACHE_DIR})
  --limit=N                      audit only first N visible places, for smoke tests
  --kakao=all|skip               verify marker locations with Kakao Local (default: all)
  --source-url=all|skip          verify source URLs with HEAD/GET (default: all)
  --kakao-concurrency=N          Kakao request concurrency (default: 4)
  --source-concurrency=N         source URL request concurrency (default: 8)
  --help                         show this help
`;
}

function parseArgs(argv) {
  const args = {
    target: 'service',
    envFile: '.env.local',
    outputDir: null,
    cacheDir: DEFAULT_CACHE_DIR,
    limit: null,
    kakao: 'all',
    sourceUrl: 'all',
    kakaoConcurrency: 4,
    sourceConcurrency: 8,
    help: false,
  };

  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg.startsWith('--target=')) {
      args.target = valueOf(arg);
    } else if (arg.startsWith('--env-file=')) {
      args.envFile = valueOf(arg);
    } else if (arg.startsWith('--output-dir=')) {
      args.outputDir = valueOf(arg);
    } else if (arg.startsWith('--cache-dir=')) {
      args.cacheDir = valueOf(arg);
    } else if (arg.startsWith('--limit=')) {
      args.limit = numberArg(arg, '--limit');
    } else if (arg.startsWith('--kakao=')) {
      args.kakao = valueOf(arg);
    } else if (arg.startsWith('--source-url=')) {
      args.sourceUrl = valueOf(arg);
    } else if (arg.startsWith('--kakao-concurrency=')) {
      args.kakaoConcurrency = numberArg(arg, '--kakao-concurrency');
    } else if (arg.startsWith('--source-concurrency=')) {
      args.sourceConcurrency = numberArg(arg, '--source-concurrency');
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!['service', 'readonly'].includes(args.target)) {
    throw new Error('--target must be service or readonly');
  }
  if (!['all', 'skip'].includes(args.kakao)) {
    throw new Error('--kakao must be all or skip');
  }
  if (!['all', 'skip'].includes(args.sourceUrl)) {
    throw new Error('--source-url must be all or skip');
  }
  return args;
}

function valueOf(arg) {
  return arg.slice(arg.indexOf('=') + 1);
}

function numberArg(arg, name) {
  const value = Number(valueOf(arg));
  if (!Number.isInteger(value) || value < 1) {
    throw new Error(`${name} must be a positive integer`);
  }
  return value;
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

function connectionStringForTarget(target, env) {
  if (target === 'readonly') return env.DATABASE_URL_READONLY;
  return env.DATABASE_URL;
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJsonFile(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return fallback;
  }
}

function writeJsonFile(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const env = { ...readDotEnv(args.envFile), ...process.env };
  const connectionString = connectionStringForTarget(args.target, env);
  if (!connectionString) {
    throw new Error(`missing DB connection string for target=${args.target}`);
  }

  const outputDir = args.outputDir ?? path.join(DEFAULT_OUTPUT_ROOT, timestamp());
  ensureDir(outputDir);
  ensureDir(args.cacheDir);

  const pool = new Pool({ connectionString, max: 1 });
  let places = [];
  let visits = [];
  let sourceRows = [];

  console.error('[marker-audit] loading visible places, visits, and sources from DB');
  try {
    await pool.query('BEGIN READ ONLY');
    await pool.query("SET LOCAL statement_timeout = '60s'");
    await pool.query("SET LOCAL lock_timeout = '3s'");

    places = await loadPlaces(pool, args.limit);
    visits = await loadVisits(pool, args.limit);
    sourceRows = await loadSources(pool, args.limit);

    await pool.query('ROLLBACK');
  } catch (error) {
    await pool.query('ROLLBACK').catch(() => {});
    throw error;
  } finally {
    await pool.end();
  }

  const visitsByPlace = groupBy(visits, 'place_id');
  const sourceStatusByUrl =
    args.sourceUrl === 'all'
      ? await verifySourceUrls(sourceRows, env, args)
      : new Map(sourceRows.map((row) => [row.url, { status: 'skipped' }]));

  const kakaoStatusByPlace =
    args.kakao === 'all'
      ? await verifyKakaoPlaces(places, env, args)
      : new Map(places.map((place) => [place.id, { status: 'skipped' }]));

  const markerRows = places.map((place) =>
    buildMarkerAuditRow(place, visitsByPlace.get(place.id) ?? [], kakaoStatusByPlace.get(place.id), sourceStatusByUrl),
  );
  const manualReviewRows = markerRows.filter((row) => row.audit_status !== 'pass');
  const summary = buildSummary({
    args,
    outputDir,
    places,
    visits,
    sourceRows,
    markerRows,
    manualReviewRows,
    sourceStatusByUrl,
  });

  const markerCsvPath = path.join(outputDir, 'markers.csv');
  const visitsCsvPath = path.join(outputDir, 'visits.csv');
  const manualReviewCsvPath = path.join(outputDir, 'manual_review.csv');
  const kakaoFailCsvPath = path.join(outputDir, 'kakao_fail.csv');
  const missingCoordinatesCsvPath = path.join(outputDir, 'missing_coordinates.csv');
  const sourceReviewCsvPath = path.join(outputDir, 'source_review.csv');
  const likelyNonPlaceCsvPath = path.join(outputDir, 'likely_non_place.csv');
  const summaryJsonPath = path.join(outputDir, 'summary.json');
  const reportPath = path.join(outputDir, 'marker-audit.md');

  writeCsv(markerCsvPath, markerRows);
  writeCsv(visitsCsvPath, visits.map((visit) => serializeVisitRow(visit, sourceStatusByUrl)));
  writeCsv(manualReviewCsvPath, manualReviewRows);
  writeCsv(kakaoFailCsvPath, markerRows.filter((row) => row.kakao_status === 'fail'));
  writeCsv(missingCoordinatesCsvPath, markerRows.filter((row) => row.latitude == null || row.longitude == null));
  writeCsv(
    sourceReviewCsvPath,
    markerRows.filter((row) => Number(row.source_url_warn_or_manual_review) > 0 || Number(row.source_url_fail) > 0),
  );
  writeCsv(likelyNonPlaceCsvPath, markerRows.filter((row) => looksLikeNonPlaceName(row.name)));
  writeJsonFile(summaryJsonPath, summary);
  fs.writeFileSync(reportPath, renderMarkdownReport(summary), 'utf8');

  console.log(
    JSON.stringify(
      {
        ok: true,
        output_dir: outputDir,
        visible_places: places.length,
        visible_visits: visits.length,
        sources: sourceRows.length,
        pass: summary.audit_status_counts.pass ?? 0,
        warn: summary.audit_status_counts.warn ?? 0,
        fail: summary.audit_status_counts.fail ?? 0,
        manual_review: summary.audit_status_counts.manual_review ?? 0,
        files: {
          report: reportPath,
          summary: summaryJsonPath,
          markers: markerCsvPath,
          visits: visitsCsvPath,
          manual_review: manualReviewCsvPath,
          kakao_fail: kakaoFailCsvPath,
          missing_coordinates: missingCoordinatesCsvPath,
          source_review: sourceReviewCsvPath,
          likely_non_place: likelyNonPlaceCsvPath,
        },
      },
      null,
      2,
    ),
  );
}

async function loadPlaces(pool, limit) {
  const limitSql = limit ? 'LIMIT $1' : '';
  const values = limit ? [limit] : [];
  const result = await pool.query(
    `
    WITH visible AS (
      SELECT
        p.id,
        p.name,
        p.kakao_place_id,
        p.natural_key,
        p.road_address,
        p.jibun_address,
        p.road_address_part,
        p.latitude,
        p.longitude,
        p.category,
        p.valid_place,
        p.is_restaurant_like,
        p.is_chain,
        p.is_large_chain,
        p.chain_brand,
        p.chain_scale,
        p.is_closed,
        p.closure_report_count,
        COALESCE(g.score, 0) AS score,
        COALESCE(g.grade, '✦') AS grade,
        g.last_visit_at,
        g.visit_count_12m,
        g.unique_department_count_12m,
        g.unique_agency_count_12m
      FROM public.places p
      LEFT JOIN public.place_grade_v1 g ON g.place_id = p.id
      WHERE p.hidden_at IS NULL
        AND p.deleted_at IS NULL
        AND p.valid_place IS TRUE
        AND p.is_restaurant_like IS TRUE
        AND p.is_large_chain IS FALSE
    ),
    visit_agg AS (
      SELECT
        v.place_id,
        COUNT(*)::integer AS total_visits,
        COUNT(*) FILTER (WHERE v.visit_date >= current_date - interval '12 months')::integer AS actual_visit_count_12m,
        COUNT(DISTINCT v.agency_id)::integer AS unique_agencies_all_time,
        COUNT(DISTINCT v.department_name)::integer AS unique_departments_all_time,
        COUNT(DISTINCT v.source_id)::integer AS source_count,
        MIN(v.visit_date)::text AS first_visit_date,
        MAX(v.visit_date)::text AS latest_visit_date,
        AVG(v.extractor_confidence)::float AS avg_extractor_confidence,
        MIN(v.extractor_confidence)::float AS min_extractor_confidence,
        COUNT(*) FILTER (WHERE v.extractor_confidence IS NULL)::integer AS missing_confidence_visits,
        COUNT(*) FILTER (WHERE v.raw_excerpt IS NULL OR btrim(v.raw_excerpt) = '')::integer AS missing_raw_excerpt_visits,
        COUNT(*) FILTER (WHERE s.url IS NULL OR btrim(s.url) = '')::integer AS missing_source_url_visits,
        COUNT(*) FILTER (WHERE s.storage_path IS NULL OR btrim(s.storage_path) = '')::integer AS missing_storage_path_visits,
        COUNT(*) FILTER (
          WHERE v.department_name ~ '^[가-힣]{2,4} (외|국장|과장|팀장|군수|시장|구청장)'
        )::integer AS masking_suspect_visits
        ,
        COUNT(*) FILTER (
          WHERE v.representative IS NOT NULL
            AND v.rank_label NOT IN (
              '시장','구청장','시의원','구의원',
              '도지사','군수','도의원','군의원'
            )
        )::integer AS representative_policy_violation_visits
      FROM public.place_visits v
      JOIN public.sources s ON s.id = v.source_id
      GROUP BY v.place_id
    )
    SELECT
      visible.*,
      COALESCE(visit_agg.total_visits, 0)::integer AS total_visits,
      COALESCE(visit_agg.actual_visit_count_12m, 0)::integer AS actual_visit_count_12m,
      COALESCE(visit_agg.unique_agencies_all_time, 0)::integer AS unique_agencies_all_time,
      COALESCE(visit_agg.unique_departments_all_time, 0)::integer AS unique_departments_all_time,
      COALESCE(visit_agg.source_count, 0)::integer AS source_count,
      visit_agg.first_visit_date,
      visit_agg.latest_visit_date,
      visit_agg.avg_extractor_confidence,
      visit_agg.min_extractor_confidence,
      COALESCE(visit_agg.missing_confidence_visits, 0)::integer AS missing_confidence_visits,
      COALESCE(visit_agg.missing_raw_excerpt_visits, 0)::integer AS missing_raw_excerpt_visits,
      COALESCE(visit_agg.missing_source_url_visits, 0)::integer AS missing_source_url_visits,
      COALESCE(visit_agg.missing_storage_path_visits, 0)::integer AS missing_storage_path_visits,
      COALESCE(visit_agg.masking_suspect_visits, 0)::integer AS masking_suspect_visits,
      COALESCE(visit_agg.representative_policy_violation_visits, 0)::integer AS representative_policy_violation_visits
    FROM visible
    LEFT JOIN visit_agg ON visit_agg.place_id = visible.id
    ORDER BY visible.score DESC NULLS LAST, visible.last_visit_at DESC NULLS LAST, visible.name ASC
    ${limitSql}
    `,
    values,
  );
  return result.rows;
}

async function loadVisits(pool, limit) {
  const limitCte = limit ? 'ORDER BY score DESC NULLS LAST, last_visit_at DESC NULLS LAST, name ASC LIMIT $1' : '';
  const values = limit ? [limit] : [];
  const result = await pool.query(
    `
    WITH visible AS (
      SELECT
        p.id,
        p.name,
        COALESCE(g.score, 0) AS score,
        g.last_visit_at
      FROM public.places p
      LEFT JOIN public.place_grade_v1 g ON g.place_id = p.id
      WHERE p.hidden_at IS NULL
        AND p.deleted_at IS NULL
        AND p.valid_place IS TRUE
        AND p.is_restaurant_like IS TRUE
        AND p.is_large_chain IS FALSE
      ${limitCte}
    )
    SELECT
      v.id AS visit_id,
      v.place_id,
      visible.name AS place_name,
      a.id AS agency_id,
      a.short_name AS agency_short_name,
      a.parent_region,
      a.sub_region,
      v.source_id,
      v.visit_date::text AS visit_date,
      v.amount,
      v.party_size,
      v.department_name,
      v.rank_label,
      v.representative,
      v.purpose,
      v.payment_method,
      v.expense_category,
      v.raw_excerpt,
      v.extractor_model,
      v.extractor_confidence::float AS extractor_confidence,
      s.url AS source_url,
      s.title AS source_title,
      s.published_at::text AS source_published_at,
      s.file_kind,
      s.storage_path,
      s.hash_sha256
    FROM public.place_visits v
    JOIN visible ON visible.id = v.place_id
    JOIN public.agencies a ON a.id = v.agency_id
    JOIN public.sources s ON s.id = v.source_id
    ORDER BY visible.score DESC NULLS LAST, v.visit_date DESC, v.id
    `,
    values,
  );
  return result.rows;
}

async function loadSources(pool, limit) {
  const limitCte = limit ? 'ORDER BY score DESC NULLS LAST, last_visit_at DESC NULLS LAST, name ASC LIMIT $1' : '';
  const values = limit ? [limit] : [];
  const result = await pool.query(
    `
    WITH visible AS (
      SELECT
        p.id,
        p.name,
        COALESCE(g.score, 0) AS score,
        g.last_visit_at
      FROM public.places p
      LEFT JOIN public.place_grade_v1 g ON g.place_id = p.id
      WHERE p.hidden_at IS NULL
        AND p.deleted_at IS NULL
        AND p.valid_place IS TRUE
        AND p.is_restaurant_like IS TRUE
        AND p.is_large_chain IS FALSE
      ${limitCte}
    )
    SELECT DISTINCT
      s.id,
      s.agency_id,
      a.short_name AS agency_short_name,
      s.url,
      s.title,
      s.published_at::text AS published_at,
      s.file_kind,
      s.storage_path,
      s.hash_sha256
    FROM public.sources s
    JOIN public.place_visits v ON v.source_id = s.id
    JOIN visible ON visible.id = v.place_id
    JOIN public.agencies a ON a.id = s.agency_id
    ORDER BY s.url
    `,
    values,
  );
  return result.rows;
}

async function verifyKakaoPlaces(places, env, args) {
  const key = env.KAKAO_REST_KEY;
  if (!key) {
    return new Map(places.map((place) => [place.id, { status: 'manual_review', reason: 'missing_kakao_rest_key' }]));
  }

  const cachePath = path.join(args.cacheDir, 'kakao-keyword-cache.json');
  const cache = readJsonFile(cachePath, {});
  const results = new Map();
  let done = 0;
  console.error(`[marker-audit] verifying ${places.length} places with Kakao Local`);

  await mapLimit(places, args.kakaoConcurrency, async (place) => {
    const queries = kakaoQueriesForPlace(place);
    const cacheKey = `${place.id}|${queries.join('|')}`;
    let payload = cache[cacheKey];
    if (!payload) {
      payload = await kakaoKeywordSearchAny(queries, key);
      cache[cacheKey] = payload;
    }
    results.set(place.id, evaluateKakaoEvidence(place, payload.documents ?? [], payload.query ?? queries[0], payload.error));
    done += 1;
    if (done % 100 === 0 || done === places.length) {
      console.error(`[marker-audit] Kakao ${done}/${places.length}`);
      writeJsonFile(cachePath, cache);
    }
  });
  writeJsonFile(cachePath, cache);
  return results;
}

function kakaoQueriesForPlace(place) {
  return unique(
    [
      [place.name, place.road_address].filter(Boolean).join(' '),
      [place.name, place.jibun_address].filter(Boolean).join(' '),
      [place.name, place.road_address_part].filter(Boolean).join(' '),
      place.name,
    ]
      .map((query) => query.trim())
      .filter(Boolean),
  );
}

async function kakaoKeywordSearchAny(queries, key) {
  let lastPayload = null;
  for (const query of queries) {
    const payload = await kakaoKeywordSearch(query, key);
    if ((payload.documents ?? []).length > 0) {
      return { ...payload, query };
    }
    lastPayload = { ...payload, query };
  }
  return lastPayload ?? { documents: [], query: queries[0] ?? '' };
}

async function kakaoKeywordSearch(query, key) {
  const url = new URL(KAKAO_KEYWORD_URL);
  url.searchParams.set('query', query);
  url.searchParams.set('size', '10');
  try {
    const response = await fetch(url, {
      headers: { Authorization: `KakaoAK ${key}` },
    });
    if (!response.ok) {
      return { documents: [], error: `kakao_${response.status}` };
    }
    return response.json();
  } catch (error) {
    return { documents: [], error: `fetch_error:${error.message}` };
  }
}

function evaluateKakaoEvidence(place, documents, query, queryError = null) {
  const storedLat = toNumber(place.latitude);
  const storedLng = toNumber(place.longitude);
  const normalizedStoredName = normalizeName(place.name);
  const storedId = place.kakao_place_id ? String(place.kakao_place_id) : null;

  const decorated = documents
    .map((doc) => {
      const lat = toNumber(doc.y);
      const lng = toNumber(doc.x);
      return {
        id: doc.id ? String(doc.id) : null,
        name: doc.place_name ?? null,
        road_address: doc.road_address_name ?? null,
        jibun_address: doc.address_name ?? null,
        category: doc.category_name ?? null,
        category_group_code: doc.category_group_code ?? null,
        distance_m:
          storedLat != null && storedLng != null && lat != null && lng != null
            ? Math.round(haversineMeters(storedLat, storedLng, lat, lng))
            : null,
        name_exact: normalizeName(doc.place_name ?? '') === normalizedStoredName,
        lat,
        lng,
      };
    })
    .sort((a, b) => scoreCandidate(place, a) - scoreCandidate(place, b));

  const exactId = storedId ? decorated.find((doc) => doc.id === storedId) : null;
  const best = exactId ?? decorated[0] ?? null;
  if (storedLat == null || storedLng == null) {
    return {
      status: 'fail',
      reason: 'missing_stored_coordinates',
      query,
      candidate_count: documents.length,
      best,
    };
  }
  if (!documents.length) {
    if (queryError) {
      return {
        status: 'manual_review',
        reason: `kakao_query_error:${queryError}`,
        query,
        candidate_count: 0,
        best: null,
      };
    }
    return {
      status: storedId ? 'fail' : 'manual_review',
      reason: storedId ? 'stored_kakao_place_not_found_by_search' : 'no_kakao_search_result',
      query,
      candidate_count: 0,
      best: null,
    };
  }
  if (!best) {
    return { status: 'manual_review', reason: 'no_usable_kakao_candidate', query, candidate_count: documents.length };
  }

  const distance = best.distance_m;
  if (storedId && exactId) {
    if (distance != null && distance <= 50) return statusFromCandidate('pass', 'stored_kakao_id_distance_within_50m', query, documents, best);
    if (distance != null && distance <= 300) return statusFromCandidate('warn', 'stored_kakao_id_distance_within_300m', query, documents, best);
    return statusFromCandidate('fail', 'stored_kakao_id_distance_over_300m_or_missing', query, documents, best);
  }

  if (storedId && !exactId) {
    if (distance != null && distance <= 100 && best.name_exact) {
      return statusFromCandidate('warn', 'stored_kakao_id_not_seen_but_name_location_match', query, documents, best);
    }
    return statusFromCandidate('fail', 'stored_kakao_id_not_seen', query, documents, best);
  }

  if (distance != null && distance <= 50 && best.name_exact) {
    return statusFromCandidate('warn', 'fallback_place_has_kakao_candidate_within_50m', query, documents, best);
  }
  if (distance != null && distance <= 300) {
    return statusFromCandidate('manual_review', 'fallback_place_candidate_within_300m', query, documents, best);
  }
  return statusFromCandidate('fail', 'kakao_candidate_distance_over_300m', query, documents, best);
}

function statusFromCandidate(status, reason, query, documents, best) {
  return {
    status,
    reason,
    query,
    candidate_count: documents.length,
    best_id: best.id,
    best_name: best.name,
    best_road_address: best.road_address,
    best_jibun_address: best.jibun_address,
    best_category: best.category,
    best_distance_m: best.distance_m,
  };
}

function scoreCandidate(place, candidate) {
  let score = 0;
  if (candidate.id && place.kakao_place_id && candidate.id === String(place.kakao_place_id)) score -= 1000;
  if (candidate.name_exact) score -= 200;
  if (candidate.category_group_code === 'FD6') score -= 50;
  if (candidate.distance_m != null) score += candidate.distance_m;
  return score;
}

async function verifySourceUrls(sourceRows, env, args) {
  const cachePath = path.join(args.cacheDir, 'source-url-cache.json');
  const cache = readJsonFile(cachePath, {});
  const byUrl = new Map();
  const rowsWithUrl = sourceRows.filter((row) => row.url);
  let done = 0;
  console.error(`[marker-audit] verifying ${rowsWithUrl.length} source URLs`);

  await mapLimit(rowsWithUrl, args.sourceConcurrency, async (row) => {
    if (!row.url) return;
    let status = cache[row.url];
    if (!status) {
      status = await verifyUrl(row.url);
      cache[row.url] = status;
    }
    byUrl.set(row.url, status);
    done += 1;
    if (done % 50 === 0 || done === rowsWithUrl.length) {
      console.error(`[marker-audit] source URLs ${done}/${rowsWithUrl.length}`);
      writeJsonFile(cachePath, cache);
    }
  });
  writeJsonFile(cachePath, cache);
  return byUrl;
}

async function verifyUrl(url) {
  const methods = ['HEAD', 'GET'];
  for (const method of methods) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, {
        method,
        redirect: 'follow',
        signal: controller.signal,
        headers: {
          'User-Agent': 'PublicOfficerMapDataAudit/1.0',
        },
      });
      clearTimeout(timeout);
      if (response.status === 405 && method === 'HEAD') continue;
      return {
        status: response.status < 400 ? 'pass' : 'warn',
        method,
        http_status: response.status,
        final_url: response.url,
        reason: response.status < 400 ? 'reachable' : 'http_error',
      };
    } catch (error) {
      clearTimeout(timeout);
      if (method === 'HEAD') continue;
      return {
        status: 'manual_review',
        method,
        http_status: null,
        final_url: null,
        reason: error?.name === 'AbortError' ? 'timeout' : `fetch_error:${error.message}`,
      };
    }
  }
  return { status: 'manual_review', reason: 'unreachable' };
}

function buildMarkerAuditRow(place, placeVisits, kakaoStatus, sourceStatusByUrl) {
  const reasons = [];
  const kakao = kakaoStatus ?? { status: 'manual_review', reason: 'missing_kakao_status' };
  const sourceUrls = new Set(placeVisits.map((visit) => visit.source_url).filter(Boolean));
  const sourceStatuses = [...sourceUrls].map((url) => sourceStatusByUrl.get(url) ?? { status: 'manual_review', reason: 'source_url_not_checked' });
  const sourceFailCount = sourceStatuses.filter((item) => item.status === 'fail').length;
  const sourceWarnCount = sourceStatuses.filter((item) => item.status === 'warn' || item.status === 'manual_review').length;

  if (!place.kakao_place_id) reasons.push('missing_kakao_place_id');
  if (place.latitude == null || place.longitude == null) reasons.push('missing_coordinates');
  if (Number(place.missing_storage_path_visits) > 0) reasons.push('missing_storage_path');
  if (Number(place.missing_source_url_visits) > 0) reasons.push('missing_source_url');
  if (Number(place.missing_raw_excerpt_visits) > 0) reasons.push('missing_raw_excerpt');
  if (Number(place.masking_suspect_visits) > 0) reasons.push('masking_suspect');
  if (Number(place.representative_policy_violation_visits) > 0) reasons.push('representative_policy_violation');
  if (toNumber(place.avg_extractor_confidence) != null && toNumber(place.avg_extractor_confidence) < 0.8) reasons.push('low_avg_confidence');
  if (kakao.status !== 'pass') reasons.push(`kakao_${kakao.status}:${kakao.reason}`);
  if (sourceFailCount > 0) reasons.push('source_url_fail');
  if (sourceWarnCount > 0) reasons.push('source_url_warn_or_manual_review');

  return {
    audit_status: classifyAuditStatus(reasons, kakao.status),
    audit_reasons: reasons.join(';'),
    place_id: place.id,
    name: place.name,
    grade: place.grade,
    score: numberString(place.score),
    total_visits: place.total_visits,
    visit_count_12m: place.visit_count_12m,
    actual_visit_count_12m: place.actual_visit_count_12m,
    unique_department_count_12m: place.unique_department_count_12m,
    unique_agency_count_12m: place.unique_agency_count_12m,
    latest_visit_date: place.latest_visit_date,
    first_visit_date: place.first_visit_date,
    road_address: place.road_address,
    jibun_address: place.jibun_address,
    road_address_part: place.road_address_part,
    latitude: place.latitude,
    longitude: place.longitude,
    category: place.category,
    kakao_place_id: place.kakao_place_id,
    natural_key: place.natural_key,
    kakao_status: kakao.status,
    kakao_reason: kakao.reason,
    kakao_query: kakao.query,
    kakao_candidate_count: kakao.candidate_count,
    kakao_best_id: kakao.best_id ?? kakao.best?.id,
    kakao_best_name: kakao.best_name ?? kakao.best?.name,
    kakao_best_road_address: kakao.best_road_address ?? kakao.best?.road_address,
    kakao_best_distance_m: kakao.best_distance_m ?? kakao.best?.distance_m,
    source_count: place.source_count,
    source_urls_checked: sourceStatuses.length,
    source_url_warn_or_manual_review: sourceWarnCount,
    source_url_fail: sourceFailCount,
    missing_source_url_visits: place.missing_source_url_visits,
    missing_storage_path_visits: place.missing_storage_path_visits,
    missing_raw_excerpt_visits: place.missing_raw_excerpt_visits,
    avg_extractor_confidence: numberString(place.avg_extractor_confidence),
    min_extractor_confidence: numberString(place.min_extractor_confidence),
    masking_suspect_visits: place.masking_suspect_visits,
    representative_policy_violation_visits: place.representative_policy_violation_visits,
    is_closed: place.is_closed,
    closure_report_count: place.closure_report_count,
  };
}

function classifyAuditStatus(reasons, kakaoStatus) {
  if (reasons.length === 0) return 'pass';
  const hardFail = reasons.some((reason) =>
    [
      'missing_coordinates',
      'missing_source_url',
      'representative_policy_violation',
      'source_url_fail',
    ].some((prefix) => reason.startsWith(prefix)),
  );
  if (hardFail || kakaoStatus === 'fail') return 'fail';
  if (reasons.some((reason) => reason.includes('manual_review'))) return 'manual_review';
  return 'warn';
}

function serializeVisitRow(visit, sourceStatusByUrl) {
  const sourceStatus = visit.source_url ? sourceStatusByUrl.get(visit.source_url) : null;
  return {
    visit_id: visit.visit_id,
    place_id: visit.place_id,
    place_name: visit.place_name,
    agency_short_name: visit.agency_short_name,
    parent_region: visit.parent_region,
    sub_region: visit.sub_region,
    visit_date: visit.visit_date,
    amount: visit.amount,
    party_size: visit.party_size,
    department_name: visit.department_name,
    rank_label: visit.rank_label,
    representative: visit.representative,
    purpose: visit.purpose,
    payment_method: visit.payment_method,
    expense_category: visit.expense_category,
    extractor_model: visit.extractor_model,
    extractor_confidence: numberString(visit.extractor_confidence),
    source_id: visit.source_id,
    source_url: visit.source_url,
    source_url_status: sourceStatus?.status ?? (visit.source_url ? 'not_checked' : 'missing'),
    source_url_reason: sourceStatus?.reason ?? null,
    source_title: visit.source_title,
    source_published_at: visit.source_published_at,
    file_kind: visit.file_kind,
    storage_path: visit.storage_path,
    hash_sha256: visit.hash_sha256,
    raw_excerpt: visit.raw_excerpt,
  };
}

function buildSummary({ args, outputDir, places, visits, sourceRows, markerRows, manualReviewRows, sourceStatusByUrl }) {
  return {
    generated_at: new Date().toISOString(),
    source_notice: SOURCE_NOTICE,
    output_dir: outputDir,
    target: args.target,
    limit: args.limit,
    visible_places: places.length,
    visible_visits: visits.length,
    sources: sourceRows.length,
    audit_status_counts: countBy(markerRows, 'audit_status'),
    grade_counts: countBy(markerRows, 'grade'),
    kakao_status_counts: countBy(markerRows, 'kakao_status'),
    source_file_kind_counts: countBy(sourceRows, 'file_kind'),
    source_url_presence_counts: countBy(visits.map((visit) => ({ status: visit.source_url ? 'present' : 'missing' })), 'status'),
    source_url_check_counts: countBy([...sourceStatusByUrl.values()], 'status'),
    places_missing_kakao_place_id: markerRows.filter((row) => !row.kakao_place_id).length,
    places_missing_coordinates: markerRows.filter((row) => row.latitude == null || row.longitude == null).length,
    places_with_any_missing_storage_path: markerRows.filter((row) => Number(row.missing_storage_path_visits) > 0).length,
    places_with_any_missing_source_url: markerRows.filter((row) => Number(row.missing_source_url_visits) > 0).length,
    places_with_low_avg_confidence: markerRows.filter((row) => row.avg_extractor_confidence !== '' && Number(row.avg_extractor_confidence) < 0.8).length,
    likely_non_place_name_count: markerRows.filter((row) => looksLikeNonPlaceName(row.name)).length,
    manual_review_count: manualReviewRows.length,
    top_reasons: topReasons(markerRows),
  };
}

function renderMarkdownReport(summary) {
  const lines = [
    '# 공무원맵 마커 단위 데이터 감사 리포트',
    '',
    `생성 시각: ${summary.generated_at}`,
    '',
    `출처 표기: ${summary.source_notice}`,
    '',
    '## 범위',
    '',
    `- target: ${summary.target}`,
    `- visible places: ${formatNumber(summary.visible_places)}`,
    `- visible visits: ${formatNumber(summary.visible_visits)}`,
    `- sources: ${formatNumber(summary.sources)}`,
    `- limit: ${summary.limit ?? 'none'}`,
    '',
    '## 판정 요약',
    '',
    '| status | places |',
    '|---|---:|',
    ...objectRows(summary.audit_status_counts),
    '',
    '## Kakao 위치 재검증',
    '',
    '| status | places |',
    '|---|---:|',
    ...objectRows(summary.kakao_status_counts),
    '',
    '## 주요 결함 카운트',
    '',
    '| 항목 | 식당 수 |',
    '|---|---:|',
    `| Kakao placeId 없음 | ${formatNumber(summary.places_missing_kakao_place_id)} |`,
    `| 좌표 없음 | ${formatNumber(summary.places_missing_coordinates)} |`,
    `| R2 원본 storage_path 누락 방문을 가진 식당 | ${formatNumber(summary.places_with_any_missing_storage_path)} |`,
    `| source_url 누락 방문을 가진 식당 | ${formatNumber(summary.places_with_any_missing_source_url)} |`,
    `| 평균 confidence < 0.8 | ${formatNumber(summary.places_with_low_avg_confidence)} |`,
    `| 목적/업무 문구가 식당명으로 들어간 의심 | ${formatNumber(summary.likely_non_place_name_count)} |`,
    '',
    '## 상위 감사 사유',
    '',
    '| reason | places |',
    '|---|---:|',
    ...summary.top_reasons.map((row) => `| ${escapeMarkdown(row.reason)} | ${formatNumber(row.count)} |`),
    '',
    '## 산출물',
    '',
    '- `markers.csv`: 마커/식당 단위 판정',
    '- `visits.csv`: 방문 기록 단위 원본 출처와 원문 발췌',
    '- `manual_review.csv`: pass가 아닌 마커만 모은 검토 큐',
    '- `kakao_fail.csv`: Kakao 위치 검증 실패 마커',
    '- `missing_coordinates.csv`: 좌표 없는 마커',
    '- `source_review.csv`: 원본 URL 현재 접근성 검토 필요 마커',
    '- `likely_non_place.csv`: 목적/업무 문구가 식당명으로 들어간 의심 마커',
    '- `summary.json`: 집계 JSON',
    '',
  ];
  return `${lines.join('\n')}\n`;
}

function objectRows(object) {
  return Object.entries(object)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `| ${escapeMarkdown(key)} | ${formatNumber(value)} |`);
}

function topReasons(rows) {
  const counts = new Map();
  for (const row of rows) {
    for (const reason of String(row.audit_reasons ?? '').split(';').filter(Boolean)) {
      counts.set(reason, (counts.get(reason) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count || a.reason.localeCompare(b.reason))
    .slice(0, 30);
}

function groupBy(rows, key) {
  const map = new Map();
  for (const row of rows) {
    const value = row[key];
    if (!map.has(value)) map.set(value, []);
    map.get(value).push(row);
  }
  return map;
}

function countBy(rows, key) {
  const counts = {};
  for (const row of rows) {
    const value = row[key] ?? 'missing';
    counts[value] = (counts[value] ?? 0) + 1;
  }
  return counts;
}

async function mapLimit(items, limit, fn) {
  let index = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (index < items.length) {
      const current = index;
      index += 1;
      await fn(items[current], current);
    }
  });
  await Promise.all(workers);
}

function writeCsv(filePath, rows) {
  if (!rows.length) {
    fs.writeFileSync(filePath, '', 'utf8');
    return;
  }
  const headers = Object.keys(rows[0]);
  const lines = [headers.join(',')];
  for (const row of rows) {
    lines.push(headers.map((header) => csvCell(row[header])).join(','));
  }
  fs.writeFileSync(filePath, `${lines.join('\n')}\n`, 'utf8');
}

function csvCell(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function normalizeName(value) {
  return String(value ?? '')
    .replace(/[\s㈜주식회사()（）·.,-]+/g, '')
    .toLowerCase();
}

function looksLikeNonPlaceName(value) {
  const text = String(value ?? '');
  if (!text) return false;
  const hints = [
    '간담회',
    '관계자',
    '현안',
    '업무',
    '협의',
    '협력',
    '논의',
    '방문',
    '민원',
    '격려',
    '의견',
    '추진',
    '점검',
    '보고',
    '워크숍',
  ];
  return hints.some((hint) => text.includes(hint));
}

function unique(values) {
  return [...new Set(values)];
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function numberString(value) {
  const number = toNumber(value);
  if (number === null) return '';
  return Number.isInteger(number) ? String(number) : number.toFixed(4);
}

function formatNumber(value) {
  return Number(value ?? 0).toLocaleString('ko-KR');
}

function escapeMarkdown(value) {
  return String(value).replaceAll('|', '\\|');
}

function haversineMeters(firstLat, firstLng, secondLat, secondLng) {
  const earthRadius = 6371000;
  const firstLatRad = radians(firstLat);
  const secondLatRad = radians(secondLat);
  const deltaLat = radians(secondLat - firstLat);
  const deltaLng = radians(secondLng - firstLng);
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(firstLatRad) * Math.cos(secondLatRad) * Math.sin(deltaLng / 2) ** 2;
  return 2 * earthRadius * Math.asin(Math.sqrt(a));
}

function radians(value) {
  return (value * Math.PI) / 180;
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }));
  process.exit(1);
});
