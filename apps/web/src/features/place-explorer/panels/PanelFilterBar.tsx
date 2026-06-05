import { ActionIcon, Checkbox, MultiSelect, Select, Tooltip } from '@mantine/core';
import { Filter, Info, List, LogIn, RotateCcw, UserRound } from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { allGrades, defaultGrades, isDefaultGradeFilter } from '../queryState';
import type { CurrentUser } from '../../auth/authApi';

const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '추천순' },
  { value: 'recent', label: '최근 방문순' },
  { value: 'visits', label: '방문 많은순' },
];

interface PanelFilterBarProps {
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
  onFilterOpen: () => void;
  onReset: () => void;
  regionLoading: boolean;
  currentUser?: CurrentUser | null;
  onLogin?: () => void;
  onLogout?: () => void;
}

export function PanelFilterBar({
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
  onFilterOpen,
  onReset,
  regionLoading,
  currentUser,
  onLogin,
  onLogout,
}: PanelFilterBarProps) {
  const publicPickSelected = isDefaultGradeFilter(selectedGrades);
  return (
    <div className="panel-filter-bar">
      <MultiSelect
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
        aria-label="정렬"
        value={sort}
        onChange={(value) => value && onSortChange(value as SortMode)}
        data={sortOptions}
        allowDeselect={false}
      />
      <Checkbox
        label="폐업 포함"
        checked={closedVisible}
        onChange={(event) => onClosedVisibleChange(event.currentTarget.checked)}
      />
      <Tooltip label="목록 열기">
        <ActionIcon variant="filled" aria-label="목록 열기" onClick={onListToggle}>
          <List size={18} />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="필터 열기">
        <ActionIcon variant="light" aria-label="필터 열기" onClick={onFilterOpen}>
          <Filter size={18} />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="필터 초기화">
        <ActionIcon variant="light" aria-label="필터 초기화" onClick={onReset}>
          <RotateCcw size={18} />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="서비스 정보">
        <ActionIcon component="a" href="/about" target="_blank" rel="noopener noreferrer" variant="light" aria-label="서비스 정보">
          <Info size={18} />
        </ActionIcon>
      </Tooltip>
      {currentUser ? (
        <Tooltip label="로그아웃">
          <button className="panel-auth-btn" onClick={onLogout} type="button">
            <UserRound size={14} />
            {currentUser.handle}
          </button>
        </Tooltip>
      ) : onLogin ? (
        <button className="panel-auth-btn" onClick={onLogin} type="button">
          <LogIn size={14} />
          로그인
        </button>
      ) : null}
    </div>
  );
}
