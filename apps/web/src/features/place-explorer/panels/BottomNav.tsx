import { Building2, Filter, House, Info, List, MapPin, MessageCircle } from 'lucide-react';
import type { MobileMode } from './BottomSheet';

interface BottomNavProps {
  mode: MobileMode;
  onChange: (mode: MobileMode) => void;
  hasSelection: boolean;
}

export function BottomNav({ mode, onChange, hasSelection }: BottomNavProps) {
  return (
    <nav className="bottom-nav" aria-label="주요 메뉴">
      <button type="button" data-active={mode === 'map'} onClick={() => onChange('map')}>
        <MapPin size={18} aria-hidden />
        지도
      </button>
      <button type="button" data-active={mode === 'list'} onClick={() => onChange('list')}>
        <List size={18} aria-hidden />
        목록
      </button>
      <button type="button" data-active={mode === 'filter'} onClick={() => onChange('filter')}>
        <Filter size={18} aria-hidden />
        필터
      </button>
      <a href="/neighborhood" className="bottom-nav-link">
        <House size={18} aria-hidden />
        살기좋은동네
      </a>
      <a href="/community" className="bottom-nav-link">
        <MessageCircle size={18} aria-hidden />
        커뮤니티
      </a>
      {hasSelection ? (
        <button type="button" data-active={mode === 'detail'} onClick={() => onChange('detail')}>
          <Building2 size={18} aria-hidden />
          상세
        </button>
      ) : (
        <a href="/about" target="_blank" rel="noopener noreferrer" className="bottom-nav-link">
          <Info size={18} aria-hidden />
          정보
        </a>
      )}
    </nav>
  );
}
