import { ActionIcon, MultiSelect, Select, Tooltip } from '@mantine/core';
import { List, LogIn, RotateCcw, UserRound } from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { allGrades, defaultGrades, isDefaultGradeFilter } from '../queryState';
import type { CurrentUser } from '../../auth/authApi';

const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '추천순' },
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
  onListToggle: () => void;
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
  onListToggle,
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
        공무원픽
      </button>

      <Select
        w={120}
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

      <Tooltip label="목록 열기/닫기">
        <button
          className="filter-chip"
          type="button"
          aria-label="목록 열기"
          onClick={onListToggle}
        >
          <List size={15} />
        </button>
      </Tooltip>

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
