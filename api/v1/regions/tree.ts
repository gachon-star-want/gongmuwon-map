import { readQuery } from '../../_lib/db';
import { publicReadRoute } from '../../_lib/route';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 국가데이터처 SGIS, 통계청 KOSIS';

type RegionRow = {
  adm_cd: string;
  level: string;
  parent_cd: string | null;
  name: string;
};

export default publicReadRoute(async () => {
  const { rows } = await readQuery<RegionRow>(
    `SELECT adm_cd, level, parent_cd, name
     FROM public.adm_regions
     WHERE level IN ('sido', 'sigungu')
     ORDER BY adm_cd`,
  );

  const sigunguByParent = new Map<string, { adm_cd: string; name: string }[]>();
  for (const row of rows) {
    if (row.level === 'sigungu' && row.parent_cd) {
      const list = sigunguByParent.get(row.parent_cd) ?? [];
      list.push({ adm_cd: row.adm_cd, name: row.name });
      sigunguByParent.set(row.parent_cd, list);
    }
  }

  const items = rows
    .filter((row) => row.level === 'sido')
    .map((sido) => ({
      adm_cd: sido.adm_cd,
      name: sido.name,
      sigungu: sigunguByParent.get(sido.adm_cd) ?? [],
    }));

  return { items, source_notice: SOURCE_NOTICE };
}, { cache: 'public, s-maxage=86400, stale-while-revalidate=604800' });
