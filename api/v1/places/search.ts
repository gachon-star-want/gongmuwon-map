import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { numberParam, stringParam } from '../../_lib/http';

const ALLOWED_GRADES = new Set(['★★★', '★★', '★', '✦']);
const ALLOWED_SORTS = new Set(['score', 'recent', 'visits']);
const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';

function splitList(raw?: string) {
  return raw
    ? raw
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
    : [];
}

function parseGrades(raw?: string) {
  const values = splitList(raw || '★★★,★★,✦');
  if (!values.every((grade) => ALLOWED_GRADES.has(grade))) return null;
  return values.length ? values : ['★★★', '★★', '✦'];
}

function orderBy(sort: string) {
  if (sort === 'recent') {
    return 'p.last_visit_at DESC NULLS LAST, p.score DESC NULLS LAST';
  }
  if (sort === 'visits') {
    return 'p.visit_count_12m DESC NULLS LAST, p.unique_department_count_12m DESC NULLS LAST, p.score DESC NULLS LAST';
  }
  return 'name_prefix_match DESC, p.score DESC NULLS LAST, p.last_visit_at DESC NULLS LAST';
}

export default publicReadRoute(async function handler({ req }) {
  const q = stringParam(req.query.q)?.trim() || null;
  const regions = splitList(stringParam(req.query.region));
  const grades = parseGrades(stringParam(req.query.grade));
  const sort = stringParam(req.query.sort) || 'score';
  const limit = Math.min(Math.max(numberParam(req.query.limit, 50), 1), 100);

  if (!grades || !ALLOWED_SORTS.has(sort)) {
    return { status: 400, body: { error: 'invalid_query' } };
  }

  const qPattern = q ? `%${q}%` : null;
  const qPrefix = q ? `${q}%` : null;
  const values = [limit, grades, regions.length ? regions : null, qPattern, qPrefix];

  const { rows } = await readQuery(
    `
    WITH visit_agg AS (
      SELECT
        place_id,
        COUNT(DISTINCT agency_id)::integer AS unique_agency_count_12m,
        ROUND(
          AVG(amount::numeric / NULLIF(party_size, 0))
          FILTER (WHERE party_size IS NOT NULL AND party_size > 0)
        )::integer AS avg_amount_per_person,
        BOOL_OR(department_name ILIKE $4) AS department_match
      FROM public.place_visits_public
      WHERE visit_date >= current_date - interval '12 months'
      GROUP BY place_id
    ),
    ranked AS (
      SELECT
        p.id,
        p.name,
        p.road_address,
        p.road_address_part,
        p.latitude,
        p.longitude,
        p.category,
        p.is_closed,
        p.closure_report_count,
        p.score,
        p.grade,
        p.last_visit_at,
        p.visit_count_12m,
        p.unique_department_count_12m,
        COALESCE(v.unique_agency_count_12m, 0) AS unique_agency_count_12m,
        v.avg_amount_per_person,
        COALESCE(p.name ILIKE $5, false) AS name_prefix_match,
        ARRAY_REMOVE(ARRAY[
          CASE WHEN $4::text IS NOT NULL AND p.name ILIKE $4 THEN 'name' END,
          CASE WHEN $4::text IS NOT NULL AND p.road_address ILIKE $4 THEN 'address' END,
          CASE WHEN $4::text IS NOT NULL AND p.category ILIKE $4 THEN 'category' END,
          CASE WHEN $4::text IS NOT NULL AND COALESCE(v.department_match, false) THEN 'department' END
        ], NULL) AS matched_fields
      FROM public.places_public p
      LEFT JOIN visit_agg v ON v.place_id = p.id
      WHERE p.grade = ANY($2::text[])
        AND ($3::text[] IS NULL OR p.road_address_part = ANY($3::text[]))
        AND (
          $4::text IS NULL
          OR p.name ILIKE $4
          OR p.road_address ILIKE $4
          OR p.category ILIKE $4
          OR COALESCE(v.department_match, false)
        )
    )
    SELECT
      id, name, road_address, road_address_part, latitude, longitude, category,
      is_closed, closure_report_count, score, grade, last_visit_at,
      visit_count_12m, unique_department_count_12m, unique_agency_count_12m,
      avg_amount_per_person, matched_fields
    FROM ranked p
    ORDER BY ${orderBy(sort)}
    LIMIT $1
    `,
    values,
  );

  return {
    items: rows,
    next_cursor: null,
    source_notice: SOURCE_NOTICE,
  };
}, { cache: true });
