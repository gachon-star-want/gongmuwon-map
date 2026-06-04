import {
  ActionIcon,
  Button,
  Checkbox,
  MultiSelect,
  Select,
  Tooltip,
} from '@mantine/core';
import {
  Filter,
  Info,
  List,
  LogIn,
  MapPin,
  MessageCircle,
  RotateCcw,
  UserRound,
} from 'lucide-react';
import type { Grade, SortMode } from '../types';
import { allGrades, defaultGrades, isDefaultGradeFilter } from '../queryState';
import type { CurrentUser } from '../../auth/authApi';
import mascotLogo from '../../../assets/officer-mascot-logo.png';

const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '추천순' },
  { value: 'recent', label: '최근 방문순' },
  { value: 'visits', label: '방문 많은순' },
];

interface FloatingSearchFilterProps {
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
  currentUser: CurrentUser | null;
  onLogin: () => void;
  onLogout: () => void;
}

export function FloatingSearchFilter({
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
}: FloatingSearchFilterProps) {
  const publicPickSelected = isDefaultGradeFilter(selectedGrades);
  return (
    <div className="floating-search">
      <a className="brand-mark" href="/" aria-label="공무원맵 홈">
        <img src={mascotLogo} alt="" aria-hidden />
        <span>공무원맵</span>
      </a>
      <nav className="map-mode-tabs" aria-label="화면 전환">
        <a href="/" data-active="true">
          <MapPin size={16} aria-hidden />
          지도
        </a>
        <a href="/community">
          <MessageCircle size={16} aria-hidden />
          커뮤니티
        </a>
      </nav>
      <MultiSelect
        className="region-select"
        data={regions}
        placeholder={regionLoading ? '자치구 로딩' : '자치구'}
        value={selectedRegions}
        onChange={onRegionsChange}
        searchable
        clearable
        maxDropdownHeight={260}
      />
      <div className="desktop-action-cluster">
        <div className="grade-chip-group" aria-label="추천 필터">
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
        <Select
          aria-label="정렬"
          className="sort-select"
          value={sort}
          onChange={(value) => value && onSortChange(value as SortMode)}
          data={sortOptions}
          allowDeselect={false}
        />
        <Checkbox
          className="desktop-closed-toggle"
          label="폐업 포함"
          checked={closedVisible}
          onChange={(event) => onClosedVisibleChange(event.currentTarget.checked)}
        />
        <div className="toolbar-icon-group">
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
              <Button className="account-chip" variant="light" leftSection={<UserRound size={15} />} onClick={onLogout}>
                {currentUser.handle}
              </Button>
            </Tooltip>
          ) : (
            <Button className="account-chip" variant="light" leftSection={<LogIn size={15} />} onClick={onLogin}>
              로그인
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
