import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { uuidParam } from '../../_lib/http';
import { normalizeAgencyRow } from '../../_lib/agencies';

export default publicReadRoute(async function handler({ req }) {
  const id = uuidParam(req.query.id);
  if (id === undefined) {
    return { status: 400, body: { error: 'missing_agency_id' } };
  }
  if (id === null) {
    return { status: 400, body: { error: 'invalid_agency_id' } };
  }
  const { rows } = await readQuery('SELECT * FROM public.agencies_public WHERE id = $1 LIMIT 1', [id]);
  if (!rows[0]) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return normalizeAgencyRow(rows[0]);
}, { cache: true });
