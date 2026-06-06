import { readQuery } from '../_lib/db';
import { publicReadRoute } from '../_lib/route';
import { numberParam, stringParam } from '../_lib/http';

const ALLOWED_GRADES = new Set(['★★★', '★★', '★', '✦']);

function parseGrades(raw?: string) {
  if (!raw) return [];
  const cleaned = raw.replace(/^in\.\(/, '').replace(/\)$/, '');
  return cleaned
    .split(',')
    .map((item) => item.trim())
    .filter((item) => ALLOWED_GRADES.has(item));
}

function parseBbox(raw?: string) {
  if (!raw) return undefined;
  const bbox = raw.split(',').map(Number);
  if (bbox.length !== 4 || !bbox.every(Number.isFinite)) return null;
  return bbox;
}

export default publicReadRoute(async function handler({ req }) {
  const bbox = parseBbox(stringParam(req.query.bbox));
  const limit = Math.min(Math.max(numberParam(req.query.limit, 100), 1), 1000);
  const grades = parseGrades(stringParam(req.query.grade));

  if (bbox === null) {
    return { status: 400, body: { error: 'invalid_bbox' } };
  }

  const values: unknown[] = [];
  const where = ['latitude IS NOT NULL', 'longitude IS NOT NULL'];

  if (bbox) {
    const start = values.length + 1;
    const [minLat, minLng, maxLat, maxLng] = bbox;
    values.push(minLat, minLng, maxLat, maxLng);
    where.push(`latitude BETWEEN $${start} AND $${start + 2}`);
    where.push(`longitude BETWEEN $${start + 1} AND $${start + 3}`);
  }

  if (grades.length) {
    values.push(grades);
    where.push(`grade = ANY($${values.length}::text[])`);
  }

  values.push(limit);
  const limitParam = values.length;

  const { rows } = await readQuery(
    `
    SELECT
      id, name, road_address, road_address_part, latitude, longitude, category,
      is_closed, closure_report_count, score, grade, last_visit_at,
      visit_count_12m, unique_department_count_12m
    FROM public.places_public
    WHERE ${where.join('\n      AND ')}
    ORDER BY score DESC NULLS LAST, last_visit_at DESC NULLS LAST
    LIMIT $${limitParam}
  `,
    values,
  );

  return rows;
}, { cache: 'public, s-maxage=1800, stale-while-revalidate=86400' });
