import { ShieldCheck } from 'lucide-react';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';

export function SourcePill({ sheetOpen = false }: { sheetOpen?: boolean }) {
  return (
    <a className="source-pill" data-sheet-open={sheetOpen} href="/legal">
      <ShieldCheck size={14} aria-hidden />
      <span>{SOURCE_NOTICE}</span>
    </a>
  );
}
