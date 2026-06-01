#!/usr/bin/env node
import fs from 'node:fs';
import process from 'node:process';
import { Pool } from 'pg';

function readDotEnv(path) {
  if (!fs.existsSync(path)) {
    return {};
  }
  return fs.readFileSync(path, 'utf8').split(/\n/).reduce((env, line) => {
    const match = line.match(/^([A-Z0-9_]+)=(")?(.*?)\2$/);
    if (match) {
      env[match[1]] = match[3];
    }
    return env;
  }, {});
}

function parseArgs(argv) {
  const args = {
    target: 'readonly',
    envFile: '.env.local',
    output: null,
  };
  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg.startsWith('--target=')) {
      args.target = arg.slice('--target='.length);
    } else if (arg.startsWith('--env-file=')) {
      args.envFile = arg.slice('--env-file='.length);
    } else if (arg.startsWith('--output=')) {
      args.output = arg.slice('--output='.length);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

function usage() {
  return `Usage: node scripts/report-db-baseline.mjs [--target=readonly|staging] [--env-file=.env.local] [--output=path]

Runs aggregate-only read-only SQL for dataset baseline/reporting.

Targets:
  readonly  Uses DATABASE_URL_READONLY only.
  staging   Uses DATABASE_URL_STAGING or STAGING_DATABASE_URL.
`;
}

function writeJson(report, outputPath) {
  const body = `${JSON.stringify(report, null, 2)}\n`;
  if (outputPath) {
    fs.writeFileSync(outputPath, body, 'utf8');
  } else {
    console.log(body.trimEnd());
  }
}

function connectionStringForTarget(target, env) {
  if (target === 'readonly') {
    return env.DATABASE_URL_READONLY;
  }
  if (target === 'staging') {
    return env.DATABASE_URL_STAGING || env.STAGING_DATABASE_URL;
  }
  throw new Error(`unsupported target: ${target}`);
}

async function maybeQuery(pool, name, sql) {
  try {
    const result = await pool.query(sql);
    return { name, ok: true, rows: result.rows };
  } catch (error) {
    return { name, ok: false, error: error.message };
  }
}

function countExpression(columnSet, column, expression) {
  if (!columnSet.has(column)) {
    return `null::int AS ${column}`;
  }
  return `${expression} AS ${column}`;
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
    throw new Error(`missing connection string for target: ${args.target}`);
  }

  const pool = new Pool({ connectionString, max: 1 });
  const report = {
    generated_at: new Date().toISOString(),
    target: args.target,
    queries: [],
  };

  try {
    await pool.query('BEGIN READ ONLY');
    await pool.query("SET LOCAL statement_timeout = '15s'");
    await pool.query("SET LOCAL lock_timeout = '2s'");

    report.queries.push(
      await maybeQuery(
        pool,
        'session',
        "SELECT current_user, current_database(), current_setting('transaction_read_only', true) AS transaction_read_only",
      ),
    );

    const columns = await pool.query(`
      SELECT table_name, column_name, data_type
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name IN (
          'agencies',
          'sources',
          'places',
          'place_visits',
          'agencies_public',
          'places_public',
          'place_visits_public'
        )
      ORDER BY table_name, ordinal_position
    `);
    report.queries.push({ name: 'columns', ok: true, rows: columns.rows });

    const byTable = new Map();
    for (const row of columns.rows) {
      if (!byTable.has(row.table_name)) {
        byTable.set(row.table_name, new Set());
      }
      byTable.get(row.table_name).add(row.column_name);
    }
    const placeColumns = byTable.get('places') ?? new Set();
    const visitColumns = byTable.get('place_visits') ?? new Set();

    report.queries.push(
      await maybeQuery(
        pool,
        'table_counts',
        `
          SELECT 'agencies' AS rel, count(*)::int AS count FROM public.agencies
          UNION ALL SELECT 'sources', count(*)::int FROM public.sources
          UNION ALL SELECT 'places', count(*)::int FROM public.places
          UNION ALL SELECT 'place_visits', count(*)::int FROM public.place_visits
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'public_view_counts',
        `
          SELECT 'agencies_public' AS rel, count(*)::int AS count FROM public.agencies_public
          UNION ALL SELECT 'places_public', count(*)::int FROM public.places_public
          UNION ALL SELECT 'place_visits_public', count(*)::int FROM public.place_visits_public
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'date_windows',
        `
          SELECT
            min(visit_date)::text AS min_visit_date,
            max(visit_date)::text AS max_visit_date,
            count(distinct visit_date)::int AS distinct_visit_dates
          FROM public.place_visits
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'monthly_visit_counts',
        `
          SELECT to_char(visit_date, 'YYYY-MM') AS ym, count(*)::int AS visits
          FROM public.place_visits
          GROUP BY ym
          ORDER BY ym
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'place_quality_counts',
        `
          SELECT
            count(*)::int AS total_places,
            count(*) FILTER (WHERE kakao_place_id IS NOT NULL)::int AS kakao_matched,
            count(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL)::int AS with_coordinates,
            ${countExpression(placeColumns, 'valid_place', "count(*) FILTER (WHERE valid_place)::int")},
            ${countExpression(placeColumns, 'is_restaurant_like', "count(*) FILTER (WHERE is_restaurant_like)::int")},
            ${countExpression(placeColumns, 'is_large_chain', "count(*) FILTER (WHERE is_large_chain)::int")},
            count(*) FILTER (WHERE hidden_at IS NOT NULL)::int AS hidden,
            count(*) FILTER (WHERE deleted_at IS NOT NULL)::int AS deleted,
            count(*) FILTER (WHERE is_closed)::int AS closed
          FROM public.places
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'visit_publicity_counts',
        `
          SELECT
            count(*)::int AS total_visits,
            count(*) FILTER (WHERE department_name IS NOT NULL)::int AS with_department,
            count(*) FILTER (WHERE rank_label IS NOT NULL)::int AS with_rank_label,
            count(*) FILTER (WHERE representative IS NOT NULL)::int AS with_representative,
            count(distinct agency_id)::int AS agencies_with_visits,
            count(distinct source_id)::int AS sources_with_visits,
            ${
              visitColumns.has('extractor_confidence')
                ? 'avg(extractor_confidence)::float AS avg_confidence'
                : 'null::float AS avg_confidence'
            }
          FROM public.place_visits
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'source_file_counts',
        `
          SELECT
            file_kind,
            count(*)::int AS count,
            min(published_at)::text AS min_published,
            max(published_at)::text AS max_published,
            count(*) FILTER (WHERE storage_path IS NULL)::int AS missing_storage_path
          FROM public.sources
          GROUP BY file_kind
          ORDER BY count DESC, file_kind
        `,
      ),
    );

    report.queries.push(
      await maybeQuery(
        pool,
        'agency_visit_distribution',
        `
          SELECT
            count(*) FILTER (WHERE visits = 0)::int AS agencies_without_visits,
            count(*) FILTER (WHERE visits > 0)::int AS agencies_with_visits,
            max(visits)::int AS max_agency_visits
          FROM (
            SELECT a.id, count(v.*) AS visits
            FROM public.agencies a
            LEFT JOIN public.place_visits v ON v.agency_id = a.id
            GROUP BY a.id
          ) agency_counts
        `,
      ),
    );

    await pool.query('ROLLBACK');
    writeJson(report, args.output);
  } catch (error) {
    await pool.query('ROLLBACK').catch(() => {});
    throw error;
  } finally {
    await pool.end();
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
});
