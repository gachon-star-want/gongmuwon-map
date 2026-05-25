import { Button, Checkbox, MultiSelect, SegmentedControl } from '@mantine/core';
import { Check } from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { gradeLabel } from '../format';

const gradeOptions = ['★★★', '★★', '✦', '★'] as const;

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
}: MobileFilterPanelProps) {
  return (
    <div className="mobile-panel">
      <div className="filter-title">필터</div>
      <MultiSelect data={regions} label="자치구" value={selectedRegions} onChange={onRegionsChange} searchable clearable />
      <div>
        <div className="panel-label">등급</div>
        <div className="grade-chip-group mobile-grade-group">
          {gradeOptions.map((grade) => {
            const selected = selectedGrades.includes(grade);
            return (
              <button
                className="filter-chip"
                data-active={selected}
                key={grade}
                type="button"
                onClick={() => {
                  if (selected && selectedGrades.length === 1) return;
                  onGradesChange(selected ? selectedGrades.filter((item) => item !== grade) : [...selectedGrades, grade]);
                }}
              >
                {selected ? <Check size={13} aria-hidden /> : null}
                {gradeLabel(grade)}
              </button>
            );
          })}
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
