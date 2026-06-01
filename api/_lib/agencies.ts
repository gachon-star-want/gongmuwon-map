import type { QueryResultRow } from 'pg';

type AgencyTaxonomy = {
  gov_tier: 'regional' | 'basic' | 'national' | 'constitutional' | 'public' | 'local_public';
  branch: 'admin' | 'council' | 'constitutional' | 'public';
  jurisdiction_type:
    | 'special_city'
    | 'metro_city'
    | 'province'
    | 'special_self_governing_city'
    | 'special_self_governing_province'
    | 'autonomous_gu'
    | 'si'
    | 'gun'
    | 'central_administrative_agency'
    | 'constitutional_institution'
    | 'independent_state_agency'
    | 'public_institution'
    | 'local_public_institution';
};

type AgencyRow = QueryResultRow & {
  kind?: string | null;
  gov_tier?: string | null;
  gov_tier_label?: string | null;
  branch?: string | null;
  branch_label?: string | null;
  jurisdiction_type?: string | null;
  jurisdiction_type_label?: string | null;
  expansion_phase?: string | null;
  expansion_phase_label?: string | null;
  parent_region?: string | null;
  sub_region?: string | null;
  short_name?: string | null;
};

const GOV_TIER_LABELS: Record<string, string> = {
  regional: '광역자치단체',
  basic: '기초자치단체',
  national: '국가기관',
  constitutional: '헌법기관',
  public: '공공기관',
  local_public: '지방공공기관',
};

const BRANCH_LABELS: Record<string, string> = {
  admin: '집행기관',
  council: '의회',
  constitutional: '헌법기관',
  public: '공공기관',
};

const JURISDICTION_TYPE_LABELS: Record<string, string> = {
  special_city: '특별시',
  metro_city: '광역시',
  province: '도',
  special_self_governing_city: '특별자치시',
  special_self_governing_province: '특별자치도',
  autonomous_gu: '자치구',
  si: '시',
  gun: '군',
  central_administrative_agency: '중앙행정기관',
  constitutional_institution: '헌법기관',
  independent_state_agency: '독립국가기관',
  public_institution: '지정 공공기관',
  local_public_institution: '지방공공기관',
};

const EXPANSION_PHASE_LABELS: Record<string, string> = {
  p1: 'P1 지방자치단체·의회',
  p2: 'P2 중앙행정기관·독립기관',
  p3: 'P3 지정 공공기관',
  p4: 'P4 지방공공기관',
};

const LEGACY_KIND_TAXONOMY: Record<string, AgencyTaxonomy> = {
  city_hall: {
    gov_tier: 'regional',
    branch: 'admin',
    jurisdiction_type: 'special_city',
  },
  city_council: {
    gov_tier: 'regional',
    branch: 'council',
    jurisdiction_type: 'special_city',
  },
  gu_office: {
    gov_tier: 'basic',
    branch: 'admin',
    jurisdiction_type: 'autonomous_gu',
  },
  gu_council: {
    gov_tier: 'basic',
    branch: 'council',
    jurisdiction_type: 'autonomous_gu',
  },
};

function compareNullableText(left: string | null | undefined, right: string | null | undefined) {
  if (!left && !right) {
    return 0;
  }
  if (!left) {
    return -1;
  }
  if (!right) {
    return 1;
  }
  return left.localeCompare(right, 'ko');
}

export function normalizeAgencyRow(row: AgencyRow) {
  const { kind, ...rest } = row;
  const legacyTaxonomy = kind ? LEGACY_KIND_TAXONOMY[kind] : undefined;
  const govTier = row.gov_tier ?? legacyTaxonomy?.gov_tier ?? null;
  const branch = row.branch ?? legacyTaxonomy?.branch ?? null;
  const jurisdictionType = row.jurisdiction_type ?? legacyTaxonomy?.jurisdiction_type ?? null;
  const expansionPhase = row.expansion_phase ?? null;

  return {
    ...rest,
    gov_tier: govTier,
    gov_tier_label: row.gov_tier_label ?? (govTier ? GOV_TIER_LABELS[govTier] : null) ?? null,
    branch,
    branch_label: row.branch_label ?? (branch ? BRANCH_LABELS[branch] : null) ?? null,
    jurisdiction_type: jurisdictionType,
    jurisdiction_type_label:
      row.jurisdiction_type_label ??
      (jurisdictionType ? JURISDICTION_TYPE_LABELS[jurisdictionType] : null) ??
      null,
    expansion_phase: expansionPhase,
    expansion_phase_label:
      row.expansion_phase_label ??
      (expansionPhase ? EXPANSION_PHASE_LABELS[expansionPhase] : null) ??
      null,
  };
}

export function normalizeAgencyRows(rows: AgencyRow[]) {
  return rows
    .map(normalizeAgencyRow)
    .sort(
      (left, right) =>
        compareNullableText(left.gov_tier, right.gov_tier) ||
        compareNullableText(left.branch, right.branch) ||
        compareNullableText(left.expansion_phase, right.expansion_phase) ||
        compareNullableText(left.parent_region, right.parent_region) ||
        compareNullableText(left.sub_region, right.sub_region) ||
        compareNullableText(left.short_name, right.short_name),
    );
}
