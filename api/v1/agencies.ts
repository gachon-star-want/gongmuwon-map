import { readQuery } from '../_lib/db';
import { publicReadRoute } from '../_lib/route';

export default publicReadRoute(async function handler({ req }) {
  const { rows } = await readQuery(
    `
    SELECT id, name, short_name, gov_tier, branch, jurisdiction_type, parent_region, sub_region, homepage,
      visit_count, place_count, last_visit_at
    FROM public.agencies_public
    ORDER BY gov_tier, branch, parent_region, sub_region NULLS FIRST, short_name
    `,
  );
  return rows;
}, { cache: true });
