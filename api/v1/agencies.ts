import { readQuery } from '../_lib/db';
import { publicReadRoute } from '../_lib/route';
import { normalizeAgencyRows } from '../_lib/agencies';

export default publicReadRoute(async function handler({ req }) {
  const { rows } = await readQuery(
    `
    SELECT *
    FROM public.agencies_public
    `,
  );
  return normalizeAgencyRows(rows);
}, { cache: true });
