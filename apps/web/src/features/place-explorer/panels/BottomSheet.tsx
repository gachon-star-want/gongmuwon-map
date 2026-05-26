import { ChevronDown } from 'lucide-react';
import type { Grade, Place, PlaceReactionSummary, SortMode, Visit } from '../types';

import { MobileFilterPanel } from './MobileFilterPanel';
import { MobileInfoPanel } from './MobileInfoPanel';
import { PlaceDetails } from './PlaceDetails';
import { PlaceList } from './PlaceList';
import { SponsorAd } from '../../ads/SponsorAd';

export type MobileMode = 'map' | 'list' | 'filter' | 'info' | 'detail';
export type SheetSize = 'peek' | 'mid' | 'full';

type BottomSheetProps = {
  mode: MobileMode;
  size: SheetSize;
  selectedPlace: Place | null;
  places: Place[];
  selectedId?: string;
  visits: Visit[];
  reactions?: PlaceReactionSummary | null;
  reactionPending?: boolean;
  loading: boolean;
  regions: { label: string; value: string }[];
  selectedRegions: string[];
  selectedGrades: Grade[];
  sort: SortMode;
  closedVisible: boolean;
  onSizeChange: (size: SheetSize) => void;
  onSelect: (place: Place) => void;
  onCloseDetail: () => void;
  onReset: () => void;
  onRegionsChange: (value: string[]) => void;
  onGradesChange: (value: Grade[]) => void;
  onSortChange: (value: SortMode) => void;
  onClosedVisibleChange: (value: boolean) => void;
  onReport: () => void;
  onClosureReport: () => void;
  onReact?: (reaction: 'like' | 'dislike') => void;
};

export function BottomSheet({
  mode,
  size,
  selectedPlace,
  places,
  selectedId,
  visits,
  reactions,
  reactionPending,
  loading,
  regions,
  selectedRegions,
  selectedGrades,
  sort,
  closedVisible,
  onSizeChange,
  onSelect,
  onCloseDetail,
  onReset,
  onRegionsChange,
  onGradesChange,
  onSortChange,
  onClosedVisibleChange,
  onReport,
  onClosureReport,
  onReact,
}: BottomSheetProps) {
  if (mode === 'map' && !selectedPlace) return null;
  const activeMode = selectedPlace && mode === 'map' ? 'detail' : mode;
  return (
    <section className="bottom-sheet" data-mode={activeMode} data-size={size} aria-label="모바일 하단 시트">
      <button
        className="sheet-handle"
        type="button"
        aria-label="시트 크기 변경"
        onClick={() => onSizeChange(size === 'full' ? 'mid' : 'full')}
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
            reactions={reactions}
            reactionPending={reactionPending}
            onReact={onReact}
          />
          <AdSlot />
        </>
      ) : null}
      {activeMode === 'list' ? (
        <>
          <PlaceList places={places} selectedId={selectedId} loading={loading} onSelect={onSelect} onReset={onReset} />
          <AdSlot />
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
        />
      ) : null}
      {activeMode === 'info' ? <MobileInfoPanel /> : null}
    </section>
  );
}

function AdSlot() {
  return <SponsorAd />;
}
