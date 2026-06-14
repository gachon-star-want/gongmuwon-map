import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';
import { stringParam } from '../../_lib/http';

// 읍면동 경계 GeoJSON(WGS84). 카카오맵 Polygon에 직접 사용. 장기 캐시.
export default publicReadRoute(async ({ req }) => {
  const admCd = stringParam(req.query.adm_cd);
  if (!admCd || !/^\d{8}$/.test(admCd)) {
    return { status: 400, body: { error: 'adm_cd_required', detail: '읍면동 8자리 코드가 필요합니다' } };
  }
  const { rows } = await readQuery<{ geojson: unknown }>(
    `SELECT geojson FROM public.region_boundaries WHERE adm_cd = $1`,
    [admCd],
  );
  if (rows.length === 0) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return rows[0].geojson;
}, { cache: 'public, s-maxage=604800, stale-while-revalidate=2592000' });
