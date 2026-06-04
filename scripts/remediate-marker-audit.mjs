#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { Pool } from 'pg';

const AUDIT_ROOT = '/private/tmp/public-officer-marker-audit';

function usage() {
  return `Usage: node scripts/remediate-marker-audit.mjs [options]

Builds remediation queues from marker audit CSVs and can apply low-risk production fixes.

Options:
  --audit-dir=path                 audit output directory; defaults to latest under ${AUDIT_ROOT}
  --queue=likely-non-place|missing-coordinates|kakao-fail|source-review|all
                                   queue to process (default: likely-non-place)
  --mode=dry-run|apply             dry-run prints candidates; apply writes supported fixes (default: dry-run)
  --target=service                 currently service only, uses DATABASE_URL
  --env-file=.env.local            dotenv file to load without printing secrets
  --limit=N                        only apply/report first N candidates
  --output=path                    write candidate JSON
  --help                           show this help
`;
}

function parseArgs(argv) {
  const args = {
    auditDir: null,
    queue: 'likely-non-place',
    mode: 'dry-run',
    target: 'service',
    envFile: '.env.local',
    limit: null,
    output: null,
    help: false,
  };
  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg.startsWith('--audit-dir=')) {
      args.auditDir = valueOf(arg);
    } else if (arg.startsWith('--queue=')) {
      args.queue = valueOf(arg);
    } else if (arg.startsWith('--mode=')) {
      args.mode = valueOf(arg);
    } else if (arg.startsWith('--target=')) {
      args.target = valueOf(arg);
    } else if (arg.startsWith('--env-file=')) {
      args.envFile = valueOf(arg);
    } else if (arg.startsWith('--limit=')) {
      args.limit = numberArg(arg, '--limit');
    } else if (arg.startsWith('--output=')) {
      args.output = valueOf(arg);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  if (!['likely-non-place', 'missing-coordinates', 'kakao-fail', 'source-review', 'all'].includes(args.queue)) {
    throw new Error('--queue is invalid');
  }
  if (!['dry-run', 'apply'].includes(args.mode)) {
    throw new Error('--mode must be dry-run or apply');
  }
  if (args.target !== 'service') {
    throw new Error('--target currently supports service only');
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

function latestAuditDir() {
  if (!fs.existsSync(AUDIT_ROOT)) {
    throw new Error(`audit root does not exist: ${AUDIT_ROOT}`);
  }
  const dirs = fs
    .readdirSync(AUDIT_ROOT)
    .map((entry) => path.join(AUDIT_ROOT, entry))
    .filter((entry) => fs.existsSync(path.join(entry, 'markers.csv')))
    .map((entry) => ({ entry, mtimeMs: fs.statSync(entry).mtimeMs }))
    .sort((a, b) => b.mtimeMs - a.mtimeMs);
  if (!dirs.length) {
    throw new Error(`no marker audit directories found under ${AUDIT_ROOT}`);
  }
  return dirs[0].entry;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const auditDir = args.auditDir ?? latestAuditDir();
  const markersPath = path.join(auditDir, 'markers.csv');
  if (!fs.existsSync(markersPath)) {
    throw new Error(`markers.csv not found: ${markersPath}`);
  }
  const markers = parseCsv(fs.readFileSync(markersPath, 'utf8'));
  const queues = buildQueues(markers);
  const selected = args.queue === 'all' ? flattenQueues(queues) : queues[args.queue];
  const candidates = args.limit ? selected.slice(0, args.limit) : selected;

  const report = {
    generated_at: new Date().toISOString(),
    audit_dir: auditDir,
    queue: args.queue,
    mode: args.mode,
    queue_counts: Object.fromEntries(Object.entries(queues).map(([key, value]) => [key, value.length])),
    candidates: candidates.map(toCandidateReportRow),
  };

  if (args.output) {
    fs.writeFileSync(args.output, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  }

  if (args.mode === 'apply') {
    if (args.queue !== 'likely-non-place') {
      throw new Error('apply currently supports only --queue=likely-non-place');
    }
    const env = { ...readDotEnv(args.envFile), ...process.env };
    if (!env.DATABASE_URL) {
      throw new Error('DATABASE_URL is required for apply mode');
    }
    report.apply = await applyLikelyNonPlace(env.DATABASE_URL, candidates);
  }

  console.log(JSON.stringify(stripLargeCandidateList(report), null, 2));
}

function stripLargeCandidateList(report) {
  return {
    ...report,
    candidates: report.candidates.slice(0, 50),
    candidate_preview_count: Math.min(report.candidates.length, 50),
    candidate_total: report.candidates.length,
  };
}

function buildQueues(markers) {
  const likelyNonPlace = markers.filter(isStrictLikelyNonPlace);
  const likelyIds = new Set(likelyNonPlace.map((row) => row.place_id));
  return {
    'likely-non-place': likelyNonPlace,
    'missing-coordinates': markers.filter(
      (row) => !likelyIds.has(row.place_id) && (!row.latitude || !row.longitude),
    ),
    'kakao-fail': markers.filter(
      (row) => !likelyIds.has(row.place_id) && row.kakao_status === 'fail' && row.latitude && row.longitude,
    ),
    'source-review': markers.filter(
      (row) => !likelyIds.has(row.place_id) && (Number(row.source_url_warn_or_manual_review) > 0 || Number(row.source_url_fail) > 0),
    ),
  };
}

function flattenQueues(queues) {
  const seen = new Set();
  const rows = [];
  for (const row of Object.values(queues).flat()) {
    if (seen.has(row.place_id)) continue;
    seen.add(row.place_id);
    rows.push(row);
  }
  return rows;
}

function isStrictLikelyNonPlace(row) {
  const name = String(row.name ?? '').trim();
  if (!name) return false;
  if (!hasPurposeLikePhrase(name)) return false;

  const evidenceWeak =
    !row.kakao_place_id ||
    !row.latitude ||
    !row.longitude ||
    row.kakao_status === 'fail' ||
    row.kakao_status === 'manual_review' ||
    name.length >= 18;

  return evidenceWeak;
}

function hasPurposeLikePhrase(name) {
  const compact = name.replace(/\s+/g, '');
  const phrasePatterns = [
    /간담회/,
    /관계자/,
    /현안/,
    /의정/,
    /의회/,
    /의원/,
    /교섭단체/,
    /위원회/,
    /집행부/,
    /공무출장/,
    /자료수집/,
    /의견수렴/,
    /업무추진/,
    /업무협의/,
    /업무수행/,
    /직원격려/,
    /격려(식비|다과비|간식|만찬|오찬)/,
    /(식비|다과비|간식구매)$/,
    /회의$/,
    /(논의|협의|추진|점검|민원|정책지원)/,
    /예산결산/,
    /군정관계자/,
    /지역특산품홍보/,
  ];
  return phrasePatterns.some((pattern) => pattern.test(compact));
}

function toCandidateReportRow(row) {
  return {
    place_id: row.place_id,
    name: row.name,
    grade: row.grade,
    score: row.score,
    total_visits: Number(row.total_visits || 0),
    visit_count_12m: Number(row.visit_count_12m || 0),
    road_address: row.road_address,
    road_address_part: row.road_address_part,
    latitude: row.latitude,
    longitude: row.longitude,
    kakao_status: row.kakao_status,
    kakao_reason: row.kakao_reason,
    audit_reasons: row.audit_reasons,
  };
}

async function applyLikelyNonPlace(databaseUrl, rows) {
  const ids = rows.map((row) => row.place_id);
  if (!ids.length) {
    return { updated: 0 };
  }
  const pool = new Pool({ connectionString: databaseUrl, max: 1 });
  try {
    await pool.query('BEGIN');
    await pool.query("SET LOCAL statement_timeout = '60s'");
    await pool.query("SET LOCAL lock_timeout = '5s'");
    const result = await pool.query(
      `
      UPDATE public.places
      SET
        valid_place = false,
        hidden_reason = COALESCE(hidden_reason, 'audit: non-place purpose/expense text extracted as place name'),
        updated_at = now()
      WHERE id = ANY($1::uuid[])
        AND hidden_at IS NULL
        AND deleted_at IS NULL
        AND valid_place IS TRUE
      RETURNING id, name
      `,
      [ids],
    );
    await pool.query('COMMIT');

    await refreshViews(pool);
    return {
      updated: result.rowCount,
      updated_preview: result.rows.slice(0, 20),
    };
  } catch (error) {
    await pool.query('ROLLBACK').catch(() => {});
    throw error;
  } finally {
    await pool.end();
  }
}

async function refreshViews(pool) {
  await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.place_grade_v1');
  await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY public.agency_stats_v1');
}

function parseCsv(text) {
  const rows = [];
  const records = [];
  let current = [];
  let field = '';
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (inQuotes) {
      if (char === '"' && next === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        field += char;
      }
      continue;
    }
    if (char === '"') {
      inQuotes = true;
    } else if (char === ',') {
      current.push(field);
      field = '';
    } else if (char === '\n') {
      current.push(field);
      records.push(current);
      current = [];
      field = '';
    } else if (char !== '\r') {
      field += char;
    }
  }
  if (field || current.length) {
    current.push(field);
    records.push(current);
  }

  const headers = records.shift() ?? [];
  for (const record of records) {
    if (!record.length || record.every((value) => value === '')) continue;
    const row = {};
    headers.forEach((header, index) => {
      row[header] = record[index] ?? '';
    });
    rows.push(row);
  }
  return rows;
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }));
  process.exit(1);
});
