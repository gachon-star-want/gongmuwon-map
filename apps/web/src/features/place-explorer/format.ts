import type { Grade, Place, SortMode } from './types';

export function sortPlaces(places: Place[], sort: SortMode): Place[] {
  return [...places].sort((a, b) => {
    if (sort === 'recent') return compareDates(b.last_visit_at, a.last_visit_at) || Number(b.score ?? 0) - Number(a.score ?? 0);
    if (sort === 'visits') {
      return (
        Number(b.visit_count_12m ?? 0) - Number(a.visit_count_12m ?? 0) ||
        Number(b.unique_department_count_12m ?? 0) - Number(a.unique_department_count_12m ?? 0)
      );
    }
    return Number(b.score ?? 0) - Number(a.score ?? 0) || compareDates(b.last_visit_at, a.last_visit_at);
  });
}

export function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const [date] = value.split('T');
  const parts = date.split('-');
  if (parts.length !== 3) return value;
  return `${parts[0]}.${parts[1]}.${parts[2]}`;
}

export function gradeLabel(grade: string): string {
  if (grade === '★★★') return '강추';
  if (grade === '★★') return '추천';
  if (grade === '★') return '중립';
  return '신규';
}

export function markerLabel(grade: string): string {
  if (grade === '★★★') return '강추';
  if (grade === '★★') return '추천';
  if (grade === '★') return '일반';
  return '신규';
}

export function gradeClass(grade: string): string {
  if (grade === '★★★') return 'top';
  if (grade === '★★') return 'good';
  if (grade === '★') return 'neutral';
  return 'new';
}

export function shortRegionLabel(region: string): string {
  const trimmed = region.trim();
  const matched = trimmed.match(/^(서울|경기|인천)\s+(.*)$/);
  return matched ? matched[2] : trimmed;
}

function compareDates(a: string | null, b: string | null) {
  return (a ? Date.parse(a) : 0) - (b ? Date.parse(b) : 0);
}

export function gradeColor(grade: Grade) {
  if (grade === '★★★') return '#dc2626'; // 강렬한 레드
  if (grade === '★★') return '#ea580c'; // 선명한 오렌지
  if (grade === '★') return '#4f46e5'; // 인디고 (그레이보다 구분됨)
  return '#0891b2'; // 시안 (신규)
}
