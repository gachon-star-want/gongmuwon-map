import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { stringParam } from '../../_lib/http';

export default publicReadRoute(async function handler({ req }) {
  const id = stringParam(req.query.id);
  if (!id) {
    return { status: 400, body: { error: 'missing_place_id' } };
  }

  const { rows } = await readQuery('SELECT * FROM public.places_public WHERE id = $1 LIMIT 1', [id]);
  if (!rows[0]) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return rows[0];
}, { cache: true });
