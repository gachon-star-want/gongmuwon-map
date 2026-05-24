import type { VercelRequest, VercelResponse } from '@vercel/node';
import { query } from '../_lib/db';
import { methodGuard, numberParam, sendJson, stringParam } from '../_lib/http';

const SEOUL_BBOX = [37.413, 126.734, 37.715, 127.269] as const;
const ALLOWED_GRADES = new Set(['★★★', '★★', '★', '✦']);

function parseGrades(raw?: string) {
  if (!raw) return [];
  const cleaned = raw.replace(/^in\.\(/, '').replace(/\)$/, '');
  return cleaned
    .split(',')
    .map((item) => item.trim())
    .filter((item) => ALLOWED_GRADES.has(item));
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!methodGuard(req, res, ['GET'])) return;

  const bbox = stringParam(req.query.bbox)?.split(',').map(Number) ?? [...SEOUL_BBOX];
  const [minLat, minLng, maxLat, maxLng] = bbox.length === 4 && bbox.every(Number.isFinite) ? bbox : SEOUL_BBOX;
  const limit = Math.min(Math.max(numberParam(req.query.limit, 100), 1), 500);
  const grades = parseGrades(stringParam(req.query.grade));

  const values: unknown[] = [minLat, minLng, maxLat, maxLng, limit];
  const gradeWhere = grades.length ? 'AND grade = ANY($6)' : '';
  if (grades.length) values.push(grades);

  const { rows } = await query(
    `
    SELECT
      id, name, road_address, road_address_part, latitude, longitude, category,
      is_closed, closure_report_count, score, grade, last_visit_at,
      visit_count_12m, unique_department_count_12m
    FROM public.places_public
    WHERE latitude BETWEEN $1 AND $3
      AND longitude BETWEEN $2 AND $4
      ${gradeWhere}
    ORDER BY score DESC NULLS LAST, last_visit_at DESC NULLS LAST
    LIMIT $5
    `,
    values,
  );

  sendJson(res, 200, rows, true);
}
