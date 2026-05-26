import type { QueryResultRow } from 'pg';

type AgencyTaxonomy = {
  gov_tier: 'regional' | 'basic';
  branch: 'admin' | 'council';
  jurisdiction_type: 'special_city' | 'autonomous_gu';
};

type AgencyRow = QueryResultRow & {
  kind?: string | null;
  gov_tier?: string | null;
  branch?: string | null;
  jurisdiction_type?: string | null;
  parent_region?: string | null;
  sub_region?: string | null;
  short_name?: string | null;
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

  return {
    ...rest,
    gov_tier: row.gov_tier ?? legacyTaxonomy?.gov_tier ?? null,
    branch: row.branch ?? legacyTaxonomy?.branch ?? null,
    jurisdiction_type: row.jurisdiction_type ?? legacyTaxonomy?.jurisdiction_type ?? null,
  };
}

export function normalizeAgencyRows(rows: AgencyRow[]) {
  return rows
    .map(normalizeAgencyRow)
    .sort(
      (left, right) =>
        compareNullableText(left.gov_tier, right.gov_tier) ||
        compareNullableText(left.branch, right.branch) ||
        compareNullableText(left.parent_region, right.parent_region) ||
        compareNullableText(left.sub_region, right.sub_region) ||
        compareNullableText(left.short_name, right.short_name),
    );
}
