import { ActionIcon, MultiSelect, Select, Tooltip } from '@mantine/core';
import { LogIn, RotateCcw, UserRound } from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { allGrades, defaultGrades, isDefaultGradeFilter } from '../queryState';
import type { CurrentUser } from '../../auth/authApi';

const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '기본 순' },
  { value: 'recent', label: '최근 방문순' },
  { value: 'visits', label: '방문 많은순' },
];

interface MapFilterBarProps {
  regions: { label: string; value: string }[];
  selectedRegions: string[];
  onRegionsChange: (value: string[]) => void;
  selectedGrades: Grade[];
  onGradesChange: (value: Grade[]) => void;
  sort: SortMode;
  onSortChange: (value: SortMode) => void;
  closedVisible: boolean;
  onClosedVisibleChange: (value: boolean) => void;
  onReset: () => void;
  regionLoading: boolean;
  currentUser?: CurrentUser | null;
  onLogin?: () => void;
  onLogout?: () => void;
}

export function MapFilterBar({
  regions,
  selectedRegions,
  onRegionsChange,
  selectedGrades,
  onGradesChange,
  sort,
  onSortChange,
  closedVisible,
  onClosedVisibleChange,
  onReset,
  regionLoading,
  currentUser,
  onLogin,
  onLogout,
}: MapFilterBarProps) {
  const publicPickSelected = isDefaultGradeFilter(selectedGrades);
  const isFilterActive =
    selectedRegions.length > 0 ||
    !publicPickSelected ||
    sort !== 'score' ||
    closedVisible;

  return (
    <div className="map-filter-bar" role="toolbar" aria-label="지도 필터 도구">
      <MultiSelect
        w={140}
        size="xs"
        style={{
          '--input-height': '32px',
          '--input-radius': '16px',
        } as React.CSSProperties}
        styles={{
          input: {
            border: '1.5px solid var(--color-border-mid)',
            background: 'rgba(255, 255, 255, 0.98)',
            fontWeight: 700,
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.06)',
            paddingTop: '2px',
            paddingBottom: '2px',
            minHeight: '32px',
          },
          pill: {
            margin: '1px 2px',
            height: '22px',
            fontSize: '11px',
            fontWeight: 600,
          }
        }}
        comboboxProps={{
          transitionProps: { transition: 'pop', duration: 150 },
          withinPortal: true,
        }}
        data={regions}
        placeholder={regionLoading ? '자치구 로딩' : '자치구'}
        value={selectedRegions}
        onChange={onRegionsChange}
        searchable
        clearable
        maxDropdownHeight={260}
      />

      <button
        className="filter-chip"
        data-active={publicPickSelected}
        type="button"
        aria-pressed={publicPickSelected}
        onClick={() => onGradesChange(publicPickSelected ? allGrades : defaultGrades)}
      >
        다회 방문
      </button>

      <Select
        w={120}
        size="xs"
        style={{
          '--input-height': '32px',
          '--input-radius': '16px',
        } as React.CSSProperties}
        styles={{
          input: {
            border: '1.5px solid var(--color-border-mid)',
            background: 'rgba(255, 255, 255, 0.98)',
            fontWeight: 700,
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.06)',
          }
        }}
        comboboxProps={{
          transitionProps: { transition: 'pop', duration: 150 },
          withinPortal: true,
        }}
        aria-label="정렬"
        value={sort}
        onChange={(value) => value && onSortChange(value as SortMode)}
        data={sortOptions}
        allowDeselect={false}
      />

      <button
        className="filter-chip"
        data-active={closedVisible}
        type="button"
        aria-pressed={closedVisible}
        onClick={() => onClosedVisibleChange(!closedVisible)}
      >
        폐업 포함
      </button>

      {isFilterActive && (
        <button
          className="filter-reset-btn"
          type="button"
          onClick={onReset}
        >
          <RotateCcw size={13} />
          <span>초기화</span>
        </button>
      )}

      {currentUser ? (
        <Tooltip label="로그아웃">
          <button className="filter-chip" onClick={onLogout} type="button">
            <UserRound size={13} />
            <span>{currentUser.handle}</span>
          </button>
        </Tooltip>
      ) : onLogin ? (
        <button className="filter-chip" onClick={onLogin} type="button">
          <LogIn size={13} />
          <span>로그인</span>
        </button>
      ) : null}
    </div>
  );
}
