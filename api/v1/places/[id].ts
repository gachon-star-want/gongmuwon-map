import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { uuidParam } from '../../_lib/http';

export default publicReadRoute(async function handler({ req }) {
  const id = uuidParam(req.query.id);
  if (id === undefined) {
    return { status: 400, body: { error: 'missing_place_id' } };
  }
  if (id === null) {
    return { status: 400, body: { error: 'invalid_place_id' } };
  }

  const { rows } = await readQuery(
    `
    SELECT
      id, name, road_address, road_address_part, latitude, longitude, category,
      is_closed, closure_report_count, score, grade, last_visit_at,
      visit_count_12m, unique_department_count_12m
    FROM public.places_public
    WHERE id = $1
    LIMIT 1
    `,
    [id],
  );
  if (!rows[0]) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return rows[0];
}, { cache: true });
