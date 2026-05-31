import { useEffect, useMemo, useState } from 'react';
import {
  ActionIcon,
  Button,
  Checkbox,
  Group,
  Modal,
  MultiSelect,
  Radio,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
  Tooltip,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  AlertTriangle,
  Building2,
  Check,
  FileText,
  Filter,
  Info,
  List,
  LogIn,
  MapPin,
  MessageCircle,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  UserRound,
  X,
} from 'lucide-react';
import type { Grade, Place, PlaceReactionSummary, Region, SortMode, Visit } from './types';
import {
  loadPlaceById as loadPlaceByIdApi,
  loadPlaceReactions as loadPlaceReactionsApi,
  loadPlaces as loadPlacesApi,
  loadRegions as loadRegionsApi,
  loadVisits as loadVisitsApi,
  searchPlaces as searchPlacesApi,
  setPlaceReaction as setPlaceReactionApi,
} from './publicData';
import { gradeLabel, shortRegionLabel, sortPlaces } from './format';
import {
  defaultGrades,
  normalizeQueryState,
  parseQueryState,
  resolveExplorerPathname,
  serializeQueryState,
  type PlaceQueryState,
} from './queryState';
import { BottomSheet, type MobileMode, type SheetSize } from './panels/BottomSheet';
import { MapCanvas } from './map/MapCanvas';
import { PlaceDetails } from './panels/PlaceDetails';
import { PlaceList } from './panels/PlaceList';
import { MobileFilterPanel } from './panels/MobileFilterPanel';
import { MobileInfoPanel } from './panels/MobileInfoPanel';
import { submitClosureReport, submitTakedownRequest } from './forms/reportFlows';
import { AuthModal } from '../auth/AuthModal';
import type { CurrentUser } from '../auth/authApi';
import { getCurrentUser, logout } from '../auth/authApi';
import { SponsorAd } from '../ads/SponsorAd';
import mascotLogo from '../../assets/officer-mascot-logo.png';
import './styles.css';

const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';
const gradeOptions = ['★★★', '★★', '✦', '★'] as const;
const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '추천순' },
  { value: 'recent', label: '최근 방문순' },
  { value: 'visits', label: '방문 많은순' },
];
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function PlaceExplorer() {
  const initialQuery = parseQueryState();
  const [queryState, setQueryState] = useState<PlaceQueryState>(() => initialQuery);
  const [searchDraft, setSearchDraft] = useState(() => initialQuery.q);
  const [places, setPlaces] = useState<Place[]>([]);
  const [searchPlaces, setSearchPlaces] = useState<Place[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [reactions, setReactions] = useState<PlaceReactionSummary | null>(null);
  const [reactionPending, setReactionPending] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [regionLoading, setRegionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [closedVisible, setClosedVisible] = useState(false);
  const [desktopListOpen, setDesktopListOpen] = useState(() => Boolean(initialQuery.q));
  const [mobileMode, setMobileMode] = useState<MobileMode>(() => initialMobileMode(initialQuery));
  const [sheetSize, setSheetSize] = useState<SheetSize>(() => (initialQuery.placeId ? 'full' : 'mid'));
  const [closureReason, setClosureReason] = useState<string | null>('방문해보니 폐업');
  const [requestCategory, setRequestCategory] = useState('식당 정보 오류');
  const [requestReason, setRequestReason] = useState('');
  const [requestEmail, setRequestEmail] = useState('');
  const [closureState, setClosureState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [requestState, setRequestState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [reportOpened, report] = useDisclosure(false);
  const [closureOpened, closure] = useDisclosure(false);
  const [authOpened, auth] = useDisclosure(false);

  const regionOptions = useMemo(() => {
    const fromApi = regions.map((region) => ({ label: region.label, value: region.region }));
    if (fromApi.length) return fromApi;
    return Array.from(new Set(places.map((place) => place.road_address_part).filter(Boolean) as string[]))
      .sort()
      .map((region) => ({ label: shortRegionLabel(region), value: region }));
  }, [places, regions]);

  const hasActiveSearchFilter = Boolean(queryState.q || queryState.region.length);
  const activeResultPlaces = hasActiveSearchFilter ? searchPlaces : places;

  const visibleResultPlaces = useMemo(() => {
    const normalizedQuery = queryState.q.trim().toLowerCase();
    return activeResultPlaces.filter((place) => {
      if (!closedVisible && place.is_closed) return false;
      if (!queryState.grade.includes(place.grade)) return false;
      if (queryState.region.length && (!place.road_address_part || !queryState.region.includes(place.road_address_part))) return false;
      if (normalizedQuery) {
        const haystack = `${place.name} ${place.road_address ?? ''} ${place.road_address_part ?? ''} ${place.category ?? ''}`.toLowerCase();
        if (!haystack.includes(normalizedQuery)) return false;
      }
      return true;
    });
  }, [activeResultPlaces, closedVisible, queryState.grade, queryState.q, queryState.region]);

  const visibleMapPlaces = useMemo(
    () => visibleResultPlaces.filter((place) => Boolean(place.latitude && place.longitude)),
    [visibleResultPlaces],
  );

  const listedPlaces = useMemo(() => {
    return sortPlaces(visibleResultPlaces, queryState.sort);
  }, [queryState.sort, visibleResultPlaces]);

  const resultLabel = useMemo(() => {
    const count = listedPlaces.length.toLocaleString('ko-KR');
    if (!hasActiveSearchFilter && !closedVisible && queryState.grade.join(',') === defaultGrades.join(',')) return `${count}곳`;
    const parts = [];
    if (queryState.q) parts.push(`"${queryState.q}"`);
    if (queryState.region.length) parts.push(`${queryState.region.length}개 자치구`);
    if (queryState.grade.join(',') !== defaultGrades.join(',')) parts.push(`${queryState.grade.length}개 등급`);
    if (closedVisible) parts.push('폐업 포함');
    return `${parts.join(' · ')} 결과 ${count}곳`;
  }, [closedVisible, hasActiveSearchFilter, listedPlaces.length, queryState.grade, queryState.q, queryState.region.length]);
  const listError = hasActiveSearchFilter ? searchError : null;
  const listLoading = hasActiveSearchFilter ? searchLoading : false;
  const hasActiveFilter = hasActiveSearchFilter || closedVisible || queryState.grade.join(',') !== defaultGrades.join(',');

  useEffect(() => {
    const onPopState = () => {
      const next = parseQueryState();
      setQueryState(next);
      setSearchDraft(next.q);
      if (!next.placeId) {
        setSelectedPlace(null);
        setMobileMode((current) => (current === 'detail' ? 'map' : current));
      }
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      const nextQ = searchDraft.trim();
      setQueryState((current) => {
        if (current.q === nextQ) return current;
        const next = { ...current, q: nextQ };
        replaceUrlState(next);
        return next;
      });
      if (nextQ) {
        setDesktopListOpen(true);
      }
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [searchDraft]);

  useEffect(() => {
    void loadPlaces();
  }, [queryState.grade]);

  useEffect(() => {
    void loadRegions();
  }, []);

  useEffect(() => {
    void getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadSearchPlaces(controller);
    return () => controller.abort();
  }, [queryState.grade, queryState.q, queryState.region, queryState.sort]);

  useEffect(() => {
    if (!queryState.placeId) {
      setSelectedPlace(null);
      return;
    }
    if (selectedPlace?.id === queryState.placeId) return;
    const local = [...places, ...searchPlaces].find((place) => place.id === queryState.placeId);
    if (local) {
      setSelectedPlace(local);
      setMobileMode('detail');
      return;
    }
    void loadPlaceById(queryState.placeId);
  }, [places, queryState.placeId, searchPlaces, selectedPlace?.id]);

  useEffect(() => {
    if (!selectedPlace) {
      setVisits([]);
      setReactions(null);
      return;
    }
    void loadVisits(selectedPlace.id);
    void loadPlaceReactions(selectedPlace.id);
  }, [selectedPlace]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      if (reportOpened || closureOpened) return;
      if (selectedPlace) {
        clearSelected();
        return;
      }
      if (desktopListOpen) {
        setDesktopListOpen(false);
        return;
      }
      if (mobileMode !== 'map') {
        setMobileMode('map');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [closureOpened, desktopListOpen, mobileMode, reportOpened, selectedPlace]);

  function updateQueryState(patch: Partial<PlaceQueryState>, mode: 'push' | 'replace' = 'push') {
    setQueryState((current) => {
      const next = normalizeQueryState({ ...current, ...patch });
      if (mode === 'replace') {
        replaceUrlState(next);
      } else {
        pushUrlState(next);
      }
      return next;
    });
  }

  async function loadPlaces() {
    setError(null);
    try {
      setPlaces(await loadPlacesApi({ grade: queryState.grade }));
    } catch {
      setError('데이터를 불러오지 못했습니다.');
    }
  }

  async function loadSearchPlaces(controller: AbortController) {
    setSearchLoading(true);
    setSearchError(null);
    setSearchPlaces([]);
    try {
      const data = await searchPlacesApi(queryState, controller.signal);
      setSearchPlaces(data.items);
    } catch (err) {
      if ((err as DOMException).name !== 'AbortError') {
        setSearchPlaces([]);
        setSearchError('검색 결과를 불러오지 못했습니다.');
      }
    } finally {
      if (!controller.signal.aborted) {
        setSearchLoading(false);
      }
    }
  }

  function retrySearch() {
    void loadSearchPlaces(new AbortController());
  }

  async function loadRegions() {
    setRegionLoading(true);
    try {
      setRegions(await loadRegionsApi());
    } catch {
      setRegions([]);
    } finally {
      setRegionLoading(false);
    }
  }

  async function loadPlaceById(placeId: string) {
    try {
      setSelectedPlace(await loadPlaceByIdApi(placeId));
      setMobileMode('detail');
    } catch {
      clearSelected('replace');
    }
  }

  async function loadVisits(placeId: string) {
    try {
      setVisits(await loadVisitsApi(placeId));
    } catch {
      setVisits([]);
    }
  }

  async function loadPlaceReactions(placeId: string) {
    try {
      setReactions(await loadPlaceReactionsApi(placeId));
    } catch {
      setReactions({ like_count: 0, dislike_count: 0, user_reaction: null });
    }
  }

  async function toggleReaction(reaction: 'like' | 'dislike') {
    if (!selectedPlace) return;
    if (!currentUser) {
      auth.open();
      return;
    }
    setReactionPending(true);
    try {
      const nextReaction = reactions?.user_reaction === reaction ? null : reaction;
      setReactions(await setPlaceReactionApi(selectedPlace.id, nextReaction));
    } catch {
      auth.open();
    } finally {
      setReactionPending(false);
    }
  }

  function selectPlace(place: Place) {
    setSelectedPlace(place);
    setMobileMode('detail');
    setSheetSize('mid');
    updateQueryState({ placeId: place.id });
  }

  function clearSelected(mode: 'push' | 'replace' = 'push') {
    setSelectedPlace(null);
    setVisits([]);
    updateQueryState({ placeId: null }, mode);
    setSheetSize('mid');
    setMobileMode((current) => (current === 'detail' ? 'map' : current));
  }

  function resetFilters() {
    setSearchDraft('');
    updateQueryState({ q: '', region: [], grade: defaultGrades, sort: 'score', placeId: null });
    setClosedVisible(false);
    setSelectedPlace(null);
    setSheetSize('mid');
    setMobileMode('map');
  }

  function changeMobileMode(mode: MobileMode) {
    setMobileMode(mode);
    if (mode === 'list') {
      setDesktopListOpen(true);
    } else if (mode === 'map' || mode === 'filter' || mode === 'info') {
      setDesktopListOpen(false);
    }
    if (mode === 'filter') {
      setSheetSize('full');
    } else {
      setSheetSize('mid');
    }
  }

  async function submitClosureReportForm() {
    if (!selectedPlace) return;
    setClosureState('submitting');
    try {
      await submitClosureReport({ placeId: selectedPlace.id, note: closureReason ?? 'web-ui-report' });
      setClosureState('done');
      await loadPlaces();
      await loadSearchPlaces(new AbortController());
    } catch {
      setClosureState('error');
    }
  }

  async function submitTakedownRequestForm() {
    if (!selectedPlace) return;
    setRequestState('submitting');
    const hiddenPlaceId = selectedPlace.id;
    try {
      const email = requestEmail.trim();
      await submitTakedownRequest({
        placeId: selectedPlace.id,
        reason: `${requestCategory}: ${requestReason.trim()}`,
        email,
      });
      setRequestState('done');
      setPlaces((current) => current.filter((place) => place.id !== hiddenPlaceId));
      setSearchPlaces((current) => current.filter((place) => place.id !== hiddenPlaceId));
      clearSelected('replace');
    } catch {
      setRequestState('error');
    }
  }

  return (
    <main className="map-experience" aria-label="공무원맵 홈">
      <MapCanvas
        places={visibleMapPlaces}
        selectedPlace={selectedPlace}
        onSelect={selectPlace}
        onBlankClick={() => {
          if (selectedPlace) clearSelected();
        }}
      />

      <section className="desktop-controls" aria-label="검색과 필터">
        <FloatingSearchFilter
          query={searchDraft}
          onQueryChange={setSearchDraft}
          regions={regionOptions}
          selectedRegions={queryState.region}
          onRegionsChange={(region) => {
            setDesktopListOpen(true);
            updateQueryState({ region });
          }}
          selectedGrades={queryState.grade}
          onGradesChange={(grade) => updateQueryState({ grade })}
          sort={queryState.sort}
          onSortChange={(sort) => updateQueryState({ sort })}
          closedVisible={closedVisible}
          onClosedVisibleChange={setClosedVisible}
          onListToggle={() => setDesktopListOpen((current) => !current)}
          onReset={resetFilters}
          regionLoading={regionLoading}
          currentUser={currentUser}
          onLogin={auth.open}
          onLogout={() =>
            void logout()
              .then(() => setCurrentUser(null))
              .catch(() => setCurrentUser(null))
          }
        />
      </section>

      <section className="mobile-search" aria-label="모바일 검색">
        <TextInput
          leftSection={<Search size={16} />}
          placeholder="식당명, 자치구, 부서 검색"
          value={searchDraft}
          onChange={(event) => setSearchDraft(event.currentTarget.value)}
          rightSection={
            searchDraft ? (
              <ActionIcon variant="subtle" aria-label="검색 지우기" onClick={() => setSearchDraft('')}>
                <X size={14} />
              </ActionIcon>
            ) : null
          }
        />
      </section>

      {error ? (
        <div className="map-status map-status-error" role="alert">
          <Text size="sm">{error}</Text>
          <Button size="xs" variant="light" leftSection={<RefreshCw size={14} />} onClick={() => void loadPlaces()}>
            다시 시도
          </Button>
        </div>
      ) : null}

      {desktopListOpen || mobileMode === 'list' ? (
        <aside className="list-sheet desktop-layer" aria-label="검색 결과 목록">
          <PlaceList
            places={listedPlaces}
            selectedId={selectedPlace?.id}
            loading={listLoading}
            error={listError}
            resultLabel={resultLabel}
            hasActiveFilter={hasActiveFilter}
            onSelect={selectPlace}
            onClose={() => {
              setDesktopListOpen(false);
              setMobileMode((current) => (current === 'list' ? 'map' : current));
            }}
            onReset={resetFilters}
            onRetry={retrySearch}
          />
          <AdSlot />
        </aside>
      ) : null}

      {mobileMode === 'filter' ? (
        <aside className="utility-sheet desktop-layer" aria-label="필터">
          <MobileFilterPanel
            regions={regionOptions}
            selectedRegions={queryState.region}
            selectedGrades={queryState.grade}
            sort={queryState.sort}
            closedVisible={closedVisible}
            onRegionsChange={(region) => updateQueryState({ region })}
            onGradesChange={(grade) => updateQueryState({ grade })}
            onSortChange={(sort) => updateQueryState({ sort })}
            onClosedVisibleChange={setClosedVisible}
            onReset={resetFilters}
            onClose={() => {
              setMobileMode('map');
              setSheetSize('mid');
            }}
          />
        </aside>
      ) : null}

      {mobileMode === 'info' ? (
        <aside className="utility-sheet info-sheet desktop-layer" aria-label="서비스 정보">
          <MobileInfoPanel />
        </aside>
      ) : null}

      {!selectedPlace && mobileMode === 'map' ? (
        <aside className="map-ad-rail desktop-layer" aria-label="광고">
          <SponsorAd variant="rail" />
        </aside>
      ) : null}

      {selectedPlace ? (
        <aside className="detail-drawer desktop-layer" aria-label="식당 상세">
          <PlaceDetails
            place={selectedPlace}
            visits={visits}
            onClose={() => clearSelected()}
            onReport={report.open}
            onClosureReport={closure.open}
            reactions={reactions}
            reactionPending={reactionPending}
            onReact={toggleReaction}
            isAuthenticated={Boolean(currentUser)}
          />
          <AdSlot />
        </aside>
      ) : null}

      <BottomSheet
        mode={mobileMode}
        size={sheetSize}
        selectedPlace={selectedPlace}
        places={listedPlaces}
        selectedId={selectedPlace?.id}
        visits={visits}
        reactions={reactions}
        reactionPending={reactionPending}
        loading={listLoading}
        error={listError}
        resultLabel={resultLabel}
        hasActiveFilter={hasActiveFilter}
        regions={regionOptions}
        selectedRegions={queryState.region}
        selectedGrades={queryState.grade}
        sort={queryState.sort}
        closedVisible={closedVisible}
        onSizeChange={setSheetSize}
        onSelect={selectPlace}
        onCloseDetail={() => clearSelected()}
        onReset={resetFilters}
        onRetry={retrySearch}
        onRegionsChange={(region) => updateQueryState({ region })}
        onGradesChange={(grade) => updateQueryState({ grade })}
        onSortChange={(sort) => updateQueryState({ sort })}
        onClosedVisibleChange={setClosedVisible}
        onCloseFilter={() => {
          setMobileMode('map');
          setSheetSize('mid');
        }}
        onReport={report.open}
        onClosureReport={closure.open}
        onReact={toggleReaction}
        isAuthenticated={Boolean(currentUser)}
      />

      <SourcePill sheetOpen={mobileMode !== 'map' || Boolean(selectedPlace)} />

      <BottomNav mode={mobileMode} onChange={changeMobileMode} hasSelection={Boolean(selectedPlace)} />

      <AuthModal opened={authOpened} onClose={auth.close} onAuthenticated={setCurrentUser} />

      <Modal
        opened={reportOpened}
        onClose={() => {
          report.close();
          setRequestCategory('식당 정보 오류');
          setRequestReason('');
          setRequestEmail('');
          setRequestState('idle');
        }}
        title="정보 수정·삭제 요청"
        centered
        trapFocus
      >
        <Stack>
          <Text size="sm" c="dimmed">
            접수 즉시 임시 비공개 처리 후 72시간 내 검토합니다.
          </Text>
          <TextInput label="식당" value={selectedPlace?.name ?? ''} readOnly />
          <Radio.Group label="사유" value={requestCategory} onChange={setRequestCategory}>
            <Stack gap={6} mt="xs">
              {['식당 정보 오류', '방문 기록 오류', '본인·소속 정보 노출 우려', '기타'].map((reason) => (
                <Radio key={reason} value={reason} label={reason} />
              ))}
            </Stack>
          </Radio.Group>
          <Textarea
            label="요청 내용"
            description="50자 이상 입력해주세요."
            placeholder="정정할 내용이나 삭제 요청 사유를 구체적으로 적어주세요."
            minRows={4}
            value={requestReason}
            onChange={(event) => setRequestReason(event.currentTarget.value)}
          />
          <TextInput
            label="이메일"
            placeholder="회신 받을 주소"
            required
            value={requestEmail}
            onChange={(event) => setRequestEmail(event.currentTarget.value)}
          />
          <Button
            leftSection={<FileText size={16} />}
            loading={requestState === 'submitting'}
            disabled={!selectedPlace || requestReason.trim().length < 50 || !EMAIL_PATTERN.test(requestEmail.trim())}
            onClick={() => void submitTakedownRequestForm()}
          >
            접수
          </Button>
          {requestState === 'done' ? <Text size="sm">접수되었습니다.</Text> : null}
          {requestState === 'error' ? (
            <Text size="sm" c="red">
              접수에 실패했습니다.
            </Text>
          ) : null}
        </Stack>
      </Modal>

      <Modal
        opened={closureOpened}
        onClose={() => {
          closure.close();
          setClosureReason('방문해보니 폐업');
          setClosureState('idle');
        }}
        title="폐업 신고"
        centered
        trapFocus
      >
        <Stack>
          <Text size="sm" c="dimmed">
            같은 브라우저의 중복 신고는 서버에서 자동 차단됩니다.
          </Text>
          <TextInput label="식당" value={selectedPlace?.name ?? ''} readOnly />
          <Select
            label="사유"
            value={closureReason}
            onChange={setClosureReason}
            data={['방문해보니 폐업', '다른 가게 입점', '장기 휴업']}
          />
          <Button
            leftSection={<AlertTriangle size={16} />}
            loading={closureState === 'submitting'}
            onClick={() => void submitClosureReportForm()}
          >
            폐업 신고 접수
          </Button>
          {closureState === 'done' ? <Text size="sm">접수되었습니다. 방문 전 확인 안내에 반영됩니다.</Text> : null}
          {closureState === 'error' ? (
            <Text size="sm" c="red">
              접수에 실패했습니다.
            </Text>
          ) : null}
        </Stack>
      </Modal>
    </main>
  );
}

function FloatingSearchFilter({
  query,
  onQueryChange,
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
}: {
  query: string;
  onQueryChange: (value: string) => void;
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
  currentUser: CurrentUser | null;
  onLogin: () => void;
  onLogout: () => void;
}) {
  return (
    <div className="floating-search">
      <a className="brand-mark" href="/" aria-label="공무원맵 홈">
        <img src={mascotLogo} alt="" aria-hidden />
        <span>공무원맵</span>
      </a>
      <TextInput
        className="search-input"
        leftSection={<Search size={16} />}
        placeholder="식당명, 자치구, 부서 검색"
        value={query}
        onChange={(event) => onQueryChange(event.currentTarget.value)}
        rightSection={
          query ? (
            <ActionIcon variant="subtle" aria-label="검색 지우기" onClick={() => onQueryChange('')}>
              <X size={14} />
            </ActionIcon>
          ) : null
        }
      />
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
        <div className="grade-chip-group" aria-label="등급 필터">
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
          <Tooltip label="필터 초기화">
            <ActionIcon variant="light" aria-label="필터 초기화" onClick={onReset}>
              <RotateCcw size={18} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="서비스 정보">
            <ActionIcon component="a" href="/about" variant="light" aria-label="서비스 정보">
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

function SourcePill({ sheetOpen = false }: { sheetOpen?: boolean }) {
  return (
    <a className="source-pill" data-sheet-open={sheetOpen} href="/legal">
      <ShieldCheck size={14} aria-hidden />
      <span>{SOURCE_NOTICE}</span>
    </a>
  );
}

function BottomNav({
  mode,
  onChange,
  hasSelection,
}: {
  mode: MobileMode;
  onChange: (mode: MobileMode) => void;
  hasSelection: boolean;
}) {
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
      <a href="/community" className="bottom-nav-link">
        <MessageCircle size={18} aria-hidden />
        커뮤니티
      </a>
      <button
        type="button"
        data-active={mode === 'info' || mode === 'detail'}
        onClick={() => onChange(hasSelection ? 'detail' : 'info')}
      >
        {hasSelection ? <Building2 size={18} aria-hidden /> : <Info size={18} aria-hidden />}
        {hasSelection ? '상세' : '정보'}
      </button>
    </nav>
  );
}

function AdSlot() {
  return <SponsorAd />;
}

function initialMobileMode(state: PlaceQueryState): MobileMode {
  if (state.placeId) return 'detail';
  if (state.q || state.region.length) return 'list';
  return 'map';
}

function pushUrlState(state: PlaceQueryState) {
  window.history.pushState(null, '', `${explorerPathname(state)}${serializeQueryState(state)}`);
}

function replaceUrlState(state: PlaceQueryState) {
  window.history.replaceState(null, '', `${explorerPathname(state)}${serializeQueryState(state)}`);
}

function explorerPathname(state: PlaceQueryState) {
  return resolveExplorerPathname(window.location.pathname, state);
}
