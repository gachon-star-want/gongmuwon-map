import { ActionIcon, Button, Checkbox, MultiSelect, SegmentedControl } from '@mantine/core';
import { X } from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { allGrades, defaultGrades, isDefaultGradeFilter } from '../queryState';

type MobileFilterPanelProps = {
  regions: { label: string; value: string }[];
  selectedRegions: string[];
  selectedGrades: Grade[];
  sort: SortMode;
  closedVisible: boolean;
  onRegionsChange: (value: string[]) => void;
  onGradesChange: (value: Grade[]) => void;
  onSortChange: (value: SortMode) => void;
  onClosedVisibleChange: (value: boolean) => void;
  onReset: () => void;
  onClose?: () => void;
};

export function MobileFilterPanel({
  regions,
  selectedRegions,
  selectedGrades,
  sort,
  closedVisible,
  onRegionsChange,
  onGradesChange,
  onSortChange,
  onClosedVisibleChange,
  onReset,
  onClose,
}: MobileFilterPanelProps) {
  const publicPickSelected = isDefaultGradeFilter(selectedGrades);
  return (
    <div className="mobile-panel">
      <div className="mobile-panel-head">
        <div className="filter-title">필터</div>
        {onClose ? (
          <ActionIcon variant="subtle" aria-label="필터 닫기" onClick={onClose}>
            <X size={18} />
          </ActionIcon>
        ) : null}
      </div>
      <MultiSelect data={regions} label="자치구" value={selectedRegions} onChange={onRegionsChange} searchable clearable />
      <div>
        <div className="panel-label">추천 신호</div>
        <div className="grade-chip-group mobile-grade-group">
          <button
            className="filter-chip public-pick-chip"
            data-active={publicPickSelected}
            type="button"
            aria-pressed={publicPickSelected}
            onClick={() => onGradesChange(publicPickSelected ? allGrades : defaultGrades)}
          >
            공무원픽
          </button>
        </div>
      </div>
      <SegmentedControl
        value={sort}
        onChange={(value) => onSortChange(value as SortMode)}
        data={[
          { value: 'score', label: '추천순' },
          { value: 'recent', label: '최근 방문순' },
          { value: 'visits', label: '방문 많은순' },
        ]}
      />
      <div className="closed-toggle">
        <Checkbox
          label="폐업 포함"
          checked={closedVisible}
          onChange={(event) => onClosedVisibleChange(event.currentTarget.checked)}
        />
      </div>
      <Button variant="light" onClick={onReset}>
        필터 초기화
      </Button>
    </div>
  );
}
