import { useRef } from 'react';
import { ChevronDown } from 'lucide-react';
import type { Grade, Place, PlaceReactionSummary, SortMode, Visit } from '../types';

import { MobileFilterPanel } from './MobileFilterPanel';
import { MobileInfoPanel } from './MobileInfoPanel';
import { PlaceDetails } from './PlaceDetails';
import { PlaceList } from './PlaceList';

export type MobileMode = 'map' | 'list' | 'filter' | 'info' | 'detail';
export type SheetSize = 'peek' | 'mid' | 'full';

type BottomSheetProps = {
  mode: MobileMode;
  size: SheetSize;
  selectedPlace: Place | null;
  places: Place[];
  selectedId?: string;
  visits: Visit[];
  loading: boolean;
  error?: string | null;
  resultLabel?: string;
  hasActiveFilter?: boolean;
  regions: { label: string; value: string }[];
  selectedRegions: string[];
  selectedGrades: Grade[];
  sort: SortMode;
  closedVisible: boolean;
  hidden?: boolean;
  onSizeChange: (size: SheetSize) => void;
  onSelect: (place: Place) => void;
  onCloseDetail: () => void;
  onReset: () => void;
  onRetry?: () => void;
  onRegionsChange: (value: string[]) => void;
  onGradesChange: (value: Grade[]) => void;
  onSortChange: (value: SortMode) => void;
  onClosedVisibleChange: (value: boolean) => void;
  onCloseFilter: () => void;
  onReport: () => void;
  onClosureReport: () => void;
};

export function BottomSheet({
  mode,
  size,
  selectedPlace,
  places,
  selectedId,
  visits,
  loading,
  error,
  resultLabel,
  hasActiveFilter,
  regions,
  selectedRegions,
  selectedGrades,
  sort,
  closedVisible,
  hidden = false,
  onSizeChange,
  onSelect,
  onCloseDetail,
  onReset,
  onRetry,
  onRegionsChange,
  onGradesChange,
  onSortChange,
  onClosedVisibleChange,
  onCloseFilter,
  onReport,
  onClosureReport,
}: BottomSheetProps) {
  const touchStartY = useRef<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (touchStartY.current === null) return;
    const currentY = e.touches[0].clientY;
    const diffY = currentY - touchStartY.current;

    // Swipe Down (아래로 쓸어내림)
    if (diffY > 60) {
      touchStartY.current = null;
      if (size === 'full') onSizeChange('mid');
      else if (size === 'mid') onSizeChange('peek');
    }
    // Swipe Up (위로 쓸어올림)
    else if (diffY < -60) {
      touchStartY.current = null;
      if (size === 'peek') onSizeChange('mid');
      else if (size === 'mid') onSizeChange('full');
    }
  };

  const handleTouchEnd = () => {
    touchStartY.current = null;
  };

  if (hidden || (mode === 'map' && !selectedPlace)) return null;
  const activeMode = selectedPlace && mode === 'map' ? 'detail' : mode;
  return (
    <section className="bottom-sheet" data-mode={activeMode} data-size={size} aria-label="모바일 하단 시트">
      <button
        className="sheet-handle"
        type="button"
        aria-label="시트 크기 변경"
        onClick={() => {
          if (size === 'full') onSizeChange('mid');
          else if (size === 'mid') onSizeChange('peek');
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <ChevronDown size={16} aria-hidden />
      </button>
      {activeMode === 'detail' && selectedPlace ? (
        <>
          <PlaceDetails
            place={selectedPlace}
            visits={visits}
            onClose={onCloseDetail}
            onReport={onReport}
            onClosureReport={onClosureReport}
          />
        </>
      ) : null}
      {activeMode === 'list' ? (
        <>
          <PlaceList
            places={places}
            selectedId={selectedId}
            loading={loading}
            error={error}
            resultLabel={resultLabel}
            hasActiveFilter={hasActiveFilter}
            onSelect={onSelect}
            onReset={onReset}
            onRetry={onRetry}
          />
        </>
      ) : null}
      {activeMode === 'filter' ? (
        <MobileFilterPanel
          regions={regions}
          selectedRegions={selectedRegions}
          selectedGrades={selectedGrades}
          sort={sort}
          closedVisible={closedVisible}
          onRegionsChange={onRegionsChange}
          onGradesChange={onGradesChange}
          onSortChange={onSortChange}
          onClosedVisibleChange={onClosedVisibleChange}
          onReset={onReset}
          onClose={onCloseFilter}
        />
      ) : null}
      {activeMode === 'info' ? <MobileInfoPanel /> : null}
    </section>
  );
}
