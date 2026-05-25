import type { VercelRequest, VercelResponse } from '@vercel/node';
import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';

export default publicReadRoute(async function handler(req: VercelRequest, res: VercelResponse) {

  const { rows } = await readQuery<{
    place_count: string;
    visit_count: string;
    agency_count: string;
    last_visit_at: string | null;
  }>(
    `
    SELECT
      (SELECT count(*) FROM public.places_public)::text AS place_count,
      (SELECT count(*) FROM public.place_visits_public)::text AS visit_count,
      (SELECT count(*) FROM public.agencies_public)::text AS agency_count,
      (SELECT max(visit_date) FROM public.place_visits_public)::text AS last_visit_at
    `,
  );

  const row = rows[0];
  return {
    place_count: Number(row.place_count),
    visit_count: Number(row.visit_count),
    agency_count: Number(row.agency_count),
    last_visit_at: row.last_visit_at,
    source_notice: '공공누리 제1유형, 출처: 서울특별시 정보소통광장 외',
  };
}, { cache: true });
