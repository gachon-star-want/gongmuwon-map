const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const cache: Record<string, { data: unknown; expiry: number }> = {};

async function getJson<T>(path: string, ttlMs: number): Promise<T> {
  const url = `${API_BASE}${path}`;
  const hit = cache[url];
  if (hit && hit.expiry > Date.now()) {
    return hit.data as T;
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${path} ${response.status}`);
  const data = (await response.json()) as T;
  cache[url] = { data, expiry: Date.now() + ttlMs };
  return data;
}

export type SidoNode = { adm_cd: string; name: string; sigungu: { adm_cd: string; name: string }[] };
export type RegionTreeResponse = { items: SidoNode[]; source_notice: string };

export type RankItem = {
  adm_cd: string;
  name: string;
  score: number;
  rank: number;
  total: number;
  solo_household_ratio: number | null;
};
export type SubregionsResponse = { household: number; items: RankItem[]; source_notice: string };

export type DetailMetric = {
  metric_key: string;
  category: string;
  display_name: string;
  unit: string | null;
  value: number;
  as_of_year: number | null;
  imputed: boolean;
};
export type NeighborhoodDetail = {
  region: { adm_cd: string; name: string; full_name: string; parent_cd: string | null };
  household: number;
  score: { score: number; rank: number; total: number; fields: number } | null;
  metrics: DetailMetric[];
  household_distribution: { size: number; households: number }[];
  fields: { category: string; percentile: number; rank: number; total: number }[];
  summary: string | null;
  evidence_poi?: {
    category: string;
    poi_type: string;
    display_name: string;
    count: number;
    distance_basis: string;
    estimated: boolean;
    source_notice: string;
  }[];
  source_notice: string;
};

const DAY = 24 * 60 * 60 * 1000;
const HOUR = 60 * 60 * 1000;

export const loadRegionTree = () => getJson<RegionTreeResponse>('/api/v1/regions/tree', DAY);

export const loadSubregions = (admCd: string, household: number) =>
  getJson<SubregionsResponse>(`/api/v1/neighborhoods/subregions?adm_cd=${admCd}&household=${household}`, HOUR);

export const loadNeighborhoodDetail = (admCd: string, household: number) =>
  getJson<NeighborhoodDetail>(`/api/v1/neighborhoods/detail?adm_cd=${admCd}&household=${household}`, HOUR);

export type BoundaryFeature = {
  type: 'Feature';
  properties: { adm_cd: string; name: string; score: number | null; rank: number | null; fields: Record<string, number> | null };
  geometry: { type: string; coordinates: unknown } | null;
};
export type BoundariesResponse = { type: 'FeatureCollection'; household: number; features: BoundaryFeature[] };

export const loadBoundaries = (admCd: string, household: number) =>
  getJson<BoundariesResponse>(`/api/v1/neighborhoods/boundaries?adm_cd=${admCd}&household=${household}`, HOUR);
