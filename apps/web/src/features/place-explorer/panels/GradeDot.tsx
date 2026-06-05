import type { Grade } from '../types';

export function GradeDot({ grade }: { grade: Grade }) {
  const cls =
    grade === '★★★' ? 'grade-top' :
    grade === '★★'  ? 'grade-good' :
    grade === '★'   ? 'grade-neutral' :
                      'grade-new';
  const label =
    grade === '★★★' ? '최상위' :
    grade === '★★'  ? '상위' :
    grade === '★'   ? '일반' : '신규';
  return (
    <span className={`grade-dot ${cls}`} aria-label={`${label} 등급`}>
      {grade}
    </span>
  );
}
