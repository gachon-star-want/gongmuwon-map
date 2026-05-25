import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActionIcon,
  Anchor,
  AppShell,
  Badge,
  Button,
  Checkbox,
  Group,
  Loader,
  Modal,
  MultiSelect,
  Radio,
  ScrollArea,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  AlertTriangle,
  Building2,
  Check,
  ChevronDown,
  Code2,
  ExternalLink,
  FileText,
  Filter,
  Info,
  Layers,
  List,
  MapPin,
  Navigation,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  X,
} from 'lucide-react';

type Grade = '★★★' | '★★' | '★' | '✦';
type SortMode = 'score' | 'recent' | 'visits';
type MobileMode = 'map' | 'list' | 'filter' | 'info' | 'detail';
type SheetSize = 'peek' | 'mid' | 'full';

type Place = {
  id: string;
  name: string;
  road_address: string | null;
  road_address_part: string | null;
  latitude: number | null;
  longitude: number | null;
  category: string | null;
  is_closed: boolean;
  closure_report_count: number;
  score: number;
  grade: Grade;
  last_visit_at: string | null;
  visit_count_12m: number | null;
  unique_department_count_12m: number | null;
  unique_agency_count_12m?: number | null;
  avg_amount_per_person?: number | null;
  matched_fields?: string[];
};

type Visit = {
  id: string;
  visit_date: string;
  amount: number;
  party_size: number | null;
  department_name: string | null;
  rank_label: string | null;
  representative: string | null;
  purpose: string | null;
  source_url: string | null;
  source_title: string | null;
};

type Region = {
  region: string;
  label: string;
  place_count: number;
  top_place_count: number;
  recommended_place_count: number;
  new_place_count: number;
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
  last_visit_at: string | null;
};

type QueryState = {
  q: string;
  region: string[];
  grade: Grade[];
  sort: SortMode;
  placeId: string | null;
};

type SearchResponse = {
  items: Place[];
  next_cursor: string | null;
  source_notice: string;
};

type RegionsResponse = {
  items: Region[];
  source_notice: string;
};

type MarkerEntry = {
  marker: any;
  place: Place;
  listener: () => void;
};

const SEOUL_BBOX = '37.413,126.734,37.715,127.269';
const SEOUL_CENTER = { latitude: 37.5665, longitude: 126.978 };
const SOURCE_NOTICE = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외';
const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;
const AD_SLOT_TEXT = (import.meta.env.VITE_AD_SLOT_TEXT as string | undefined)?.trim();
const AD_SLOT_URL = (import.meta.env.VITE_AD_SLOT_URL as string | undefined)?.trim();
const gradeOptions = ['★★★', '★★', '✦', '★'] as const;
const defaultGrades: Grade[] = ['★★★', '★★', '✦'];
const sortOptions: { value: SortMode; label: string }[] = [
  { value: 'score', label: '추천순' },
  { value: 'recent', label: '최근 방문순' },
  { value: 'visits', label: '방문 많은순' },
];
const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

export function App() {
  const path = window.location.pathname;
  if (staticPaths.has(path)) {
    return <StaticPage path={path} />;
  }
  return <MapExperience />;
}

function MapExperience() {
  const [queryState, setQueryState] = useState<QueryState>(() => parseQueryState());
  const [searchDraft, setSearchDraft] = useState(() => parseQueryState().q);
  const [places, setPlaces] = useState<Place[]>([]);
  const [searchPlaces, setSearchPlaces] = useState<Place[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [regionLoading, setRegionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [closedVisible, setClosedVisible] = useState(false);
  const [desktopListOpen, setDesktopListOpen] = useState(() => Boolean(parseQueryState().q));
  const [mobileMode, setMobileMode] = useState<MobileMode>(() => initialMobileMode(parseQueryState()));
  const [sheetSize, setSheetSize] = useState<SheetSize>(() => (parseQueryState().placeId ? 'full' : 'mid'));
  const [closureReason, setClosureReason] = useState<string | null>('방문해보니 폐업');
  const [requestCategory, setRequestCategory] = useState('식당 정보 오류');
  const [requestReason, setRequestReason] = useState('');
  const [requestEmail, setRequestEmail] = useState('');
  const [closureState, setClosureState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [requestState, setRequestState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');
  const [reportOpened, report] = useDisclosure(false);
  const [closureOpened, closure] = useDisclosure(false);

  const regionOptions = useMemo(() => {
    const fromApi = regions.map((region) => ({ label: region.label, value: region.region }));
    if (fromApi.length) return fromApi;
    return Array.from(new Set(places.map((place) => place.road_address_part).filter(Boolean) as string[]))
      .sort()
      .map((region) => ({ label: shortRegionLabel(region), value: region }));
  }, [places, regions]);

  const visibleMapPlaces = useMemo(() => {
    const normalizedQuery = queryState.q.trim().toLowerCase();
    return places.filter((place) => {
      if (!closedVisible && place.is_closed) return false;
      if (!queryState.grade.includes(place.grade)) return false;
      if (queryState.region.length && (!place.road_address_part || !queryState.region.includes(place.road_address_part))) {
        return false;
      }
      if (normalizedQuery) {
        const haystack = `${place.name} ${place.road_address ?? ''} ${place.road_address_part ?? ''} ${place.category ?? ''}`.toLowerCase();
        if (!haystack.includes(normalizedQuery)) return false;
      }
      return Boolean(place.latitude && place.longitude);
    });
  }, [closedVisible, places, queryState.grade, queryState.q, queryState.region]);

  const listedPlaces = useMemo(() => {
    const source = searchPlaces.length || searchLoading ? searchPlaces : visibleMapPlaces;
    const filtered = source.filter((place) => closedVisible || !place.is_closed);
    return sortPlaces(filtered, queryState.sort);
  }, [closedVisible, queryState.sort, searchLoading, searchPlaces, visibleMapPlaces]);

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
      return;
    }
    void loadVisits(selectedPlace.id);
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

  function updateQueryState(patch: Partial<QueryState>, mode: 'push' | 'replace' = 'push') {
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
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        bbox: SEOUL_BBOX,
        grade: queryState.grade.join(','),
        limit: '500',
      });
      const response = await fetch(apiUrl(`/api/v1/places?${params.toString()}`));
      if (!response.ok) throw new Error(`places ${response.status}`);
      const data = (await response.json()) as Place[];
      setPlaces(data);
    } catch {
      setError('데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }

  async function loadSearchPlaces(controller: AbortController) {
    setSearchLoading(true);
    try {
      const params = new URLSearchParams({
        limit: '100',
        sort: queryState.sort,
        grade: queryState.grade.join(','),
      });
      if (queryState.q) params.set('q', queryState.q);
      if (queryState.region.length) params.set('region', queryState.region.join(','));
      const response = await fetch(apiUrl(`/api/v1/places/search?${params.toString()}`), {
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`search ${response.status}`);
      const data = (await response.json()) as SearchResponse;
      setSearchPlaces(data.items);
    } catch (err) {
      if ((err as DOMException).name !== 'AbortError') {
        setSearchPlaces([]);
      }
    } finally {
      if (!controller.signal.aborted) {
        setSearchLoading(false);
      }
    }
  }

  async function loadRegions() {
    setRegionLoading(true);
    try {
      const response = await fetch(apiUrl('/api/v1/regions'));
      if (!response.ok) throw new Error(`regions ${response.status}`);
      const data = (await response.json()) as RegionsResponse;
      setRegions(data.items);
    } catch {
      setRegions([]);
    } finally {
      setRegionLoading(false);
    }
  }

  async function loadPlaceById(placeId: string) {
    try {
      const response = await fetch(apiUrl(`/api/v1/places/${placeId}`));
      if (!response.ok) throw new Error(`place ${response.status}`);
      setSelectedPlace((await response.json()) as Place);
      setMobileMode('detail');
    } catch {
      clearSelected('replace');
    }
  }

  async function loadVisits(placeId: string) {
    try {
      const response = await fetch(apiUrl(`/api/v1/places/${placeId}/visits?limit=50`));
      if (!response.ok) throw new Error(`visits ${response.status}`);
      setVisits((await response.json()) as Visit[]);
    } catch {
      setVisits([]);
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
    if (mode === 'filter') {
      setSheetSize('full');
    } else if (mode === 'map') {
      setSheetSize('mid');
    } else {
      setSheetSize('mid');
    }
  }

  async function submitClosureReport() {
    if (!selectedPlace) return;
    setClosureState('submitting');
    try {
      const response = await fetch(apiUrl('/api/closure-report'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place_id: selectedPlace.id,
          reporter_fp: browserFingerprint(),
          note: closureReason ?? 'web-ui-report',
        }),
      });
      if (!response.ok) throw new Error(`closure ${response.status}`);
      setClosureState('done');
      await loadPlaces();
      await loadSearchPlaces(new AbortController());
    } catch {
      setClosureState('error');
    }
  }

  async function submitTakedownRequest() {
    if (!selectedPlace) return;
    setRequestState('submitting');
    const hiddenPlaceId = selectedPlace.id;
    try {
      const response = await fetch(apiUrl('/api/takedown-request'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place_id: selectedPlace.id,
          reason: `${requestCategory}: ${requestReason.trim()}`,
          email: requestEmail.trim() || null,
        }),
      });
      if (!response.ok) throw new Error(`takedown ${response.status}`);
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
          onListToggle={() => setDesktopListOpen((current) => !current)}
          onReset={resetFilters}
          regionLoading={regionLoading}
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

      {loading ? (
        <div className="map-status" role="status">
          <Loader size="sm" />
          <Text size="sm">지도 데이터를 불러오는 중입니다.</Text>
        </div>
      ) : null}

      {error ? (
        <div className="map-status map-status-error" role="alert">
          <Text size="sm">{error}</Text>
          <Button size="xs" variant="light" leftSection={<RefreshCw size={14} />} onClick={() => void loadPlaces()}>
            다시 시도
          </Button>
        </div>
      ) : null}

      {desktopListOpen ? (
        <aside className="list-sheet desktop-layer" aria-label="검색 결과 목록">
          <PlaceList
            places={listedPlaces}
            selectedId={selectedPlace?.id}
            loading={searchLoading}
            onSelect={selectPlace}
            onClose={() => setDesktopListOpen(false)}
            onReset={resetFilters}
          />
          <AdSlot />
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
        loading={searchLoading}
        regions={regionOptions}
        selectedRegions={queryState.region}
        selectedGrades={queryState.grade}
        sort={queryState.sort}
        closedVisible={closedVisible}
        onSizeChange={setSheetSize}
        onSelect={selectPlace}
        onCloseDetail={() => clearSelected()}
        onReset={resetFilters}
        onRegionsChange={(region) => updateQueryState({ region })}
        onGradesChange={(grade) => updateQueryState({ grade })}
        onSortChange={(sort) => updateQueryState({ sort })}
        onClosedVisibleChange={setClosedVisible}
        onReport={report.open}
        onClosureReport={closure.open}
      />

      <SourcePill sheetOpen={mobileMode !== 'map' || Boolean(selectedPlace)} />

      <BottomNav mode={mobileMode} onChange={changeMobileMode} hasSelection={Boolean(selectedPlace)} />

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
            value={requestEmail}
            onChange={(event) => setRequestEmail(event.currentTarget.value)}
          />
          <Button
            loading={requestState === 'submitting'}
            disabled={!selectedPlace || requestReason.trim().length < 50}
            leftSection={<AlertTriangle size={16} />}
            onClick={() => void submitTakedownRequest()}
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
            loading={closureState === 'submitting'}
            leftSection={<AlertTriangle size={16} />}
            onClick={() => void submitClosureReport()}
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
  onListToggle,
  onReset,
  regionLoading,
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
  onListToggle: () => void;
  onReset: () => void;
  regionLoading: boolean;
}) {
  return (
    <div className="floating-search">
      <a className="brand-mark" href="/" aria-label="공무원맵 홈">
        <MapPin size={20} aria-hidden />
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
      <SegmentedControl
        className="sort-control"
        value={sort}
        onChange={(value) => onSortChange(value as SortMode)}
        data={sortOptions}
      />
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
    </div>
  );
}

function PlaceList({
  places,
  selectedId,
  loading,
  onSelect,
  onClose,
  onReset,
}: {
  places: Place[];
  selectedId?: string;
  loading: boolean;
  onSelect: (place: Place) => void;
  onClose?: () => void;
  onReset: () => void;
}) {
  return (
    <div className="sheet-content">
      <Group justify="space-between" wrap="nowrap" className="sheet-header">
        <div>
          <Text fw={800}>식당 목록</Text>
          <Text size="xs" c="dimmed">
            {loading ? '검색 중' : `${places.length.toLocaleString('ko-KR')}곳`}
          </Text>
        </div>
        {onClose ? (
          <ActionIcon variant="subtle" aria-label="목록 닫기" onClick={onClose}>
            <X size={18} />
          </ActionIcon>
        ) : null}
      </Group>
      {loading ? (
        <div className="sheet-empty">
          <Loader size="sm" />
        </div>
      ) : places.length ? (
        <ScrollArea className="sheet-scroll">
          <Stack gap={6} p="xs">
            {places.map((place) => (
              <button
                className="place-row"
                data-active={place.id === selectedId}
                key={place.id}
                type="button"
                onClick={() => onSelect(place)}
              >
                <span className={`grade-dot grade-${gradeClass(place.grade)}`}>{markerLabel(place.grade)}</span>
                <span className="place-row-body">
                  <strong>{place.name}</strong>
                  <small>{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</small>
                  <span>
                    {place.visit_count_12m ?? 0}회 · 최근 {formatDate(place.last_visit_at) ?? '확인 중'}
                  </span>
                </span>
              </button>
            ))}
          </Stack>
        </ScrollArea>
      ) : (
        <div className="sheet-empty">
          <Text fw={700}>조건에 맞는 식당이 없습니다.</Text>
          <Button size="xs" variant="light" leftSection={<RotateCcw size={14} />} onClick={onReset}>
            필터 초기화
          </Button>
        </div>
      )}
    </div>
  );
}

function PlaceDetails({
  place,
  visits,
  onClose,
  onReport,
  onClosureReport,
}: {
  place: Place;
  visits: Visit[];
  onClose: () => void;
  onReport: () => void;
  onClosureReport: () => void;
}) {
  const kakaoUrl = `https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`;
  return (
    <div className="detail-content">
      <Group justify="space-between" wrap="nowrap" className="detail-header">
        <Group gap={6}>
          <Badge className={`grade-badge grade-${gradeClass(place.grade)}`}>{gradeLabel(place.grade)}</Badge>
          {place.is_closed ? <Badge color="gray">폐업</Badge> : null}
          {!place.is_closed && place.closure_report_count > 0 ? (
            <Badge color="yellow">폐업 제보 {place.closure_report_count}건</Badge>
          ) : null}
        </Group>
        <ActionIcon variant="subtle" aria-label="상세 닫기" onClick={onClose}>
          <X size={18} />
        </ActionIcon>
      </Group>

      {place.closure_report_count > 0 && !place.is_closed ? (
        <div className="warning-banner">
          <AlertTriangle size={16} aria-hidden />
          폐업 제보 {place.closure_report_count}건 - 방문 전 확인 권장
        </div>
      ) : null}

      <section className="detail-section detail-title">
        <Title order={2}>{place.name}</Title>
        <Text c="dimmed">{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</Text>
      </section>

      <section className="detail-section">
        <Text size="sm" fw={700}>
          방문 빈도와 부서 다양성 기반 통계 신호입니다.
        </Text>
        <div className="stat-grid">
          <Metric label="방문" value={`${place.visit_count_12m ?? 0}회`} />
          <Metric label="부서" value={`${place.unique_department_count_12m ?? 0}개`} />
          <Metric label="최근" value={formatDate(place.last_visit_at) ?? '확인 중'} />
          {place.avg_amount_per_person ? (
            <Metric label="평균 1인당" value={`${place.avg_amount_per_person.toLocaleString('ko-KR')}원`} />
          ) : null}
        </div>
      </section>

      <section className="detail-section">
        <Text fw={800}>방문 기록</Text>
        {visits.length ? (
          <Stack gap={0} mt="xs">
            {visits.slice(0, 10).map((visit) => (
              <a className="visit-row" href={visit.source_url ?? '#'} target="_blank" rel="noreferrer" key={visit.id}>
                <span>{formatDate(visit.visit_date) ?? visit.visit_date}</span>
                <strong>{visit.amount.toLocaleString('ko-KR')}원</strong>
                <small>{[visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ')}</small>
                <small className="source-link">
                  <ExternalLink size={13} aria-hidden /> 원문 보기
                </small>
              </a>
            ))}
          </Stack>
        ) : (
          <Text size="sm" c="dimmed" mt="xs">
            방문 기록을 불러오는 중이거나 공개된 기록이 없습니다.
          </Text>
        )}
      </section>

      <section className="detail-section detail-actions">
        <Button component="a" href={kakaoUrl} target="_blank" rel="noreferrer" leftSection={<Navigation size={16} />}>
          카카오맵에서 보기
        </Button>
        <Button variant="light" leftSection={<FileText size={16} />} onClick={onReport}>
          정보 수정·삭제 요청
        </Button>
        <Button variant="outline" color="gray" leftSection={<AlertTriangle size={16} />} onClick={onClosureReport}>
          폐업 신고
        </Button>
      </section>
    </div>
  );
}

function BottomSheet({
  mode,
  size,
  selectedPlace,
  places,
  selectedId,
  visits,
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
}: {
  mode: MobileMode;
  size: SheetSize;
  selectedPlace: Place | null;
  places: Place[];
  selectedId?: string;
  visits: Visit[];
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
}) {
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

function MobileFilterPanel({
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
}: {
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
}) {
  return (
    <div className="mobile-panel">
      <Text fw={800}>필터</Text>
      <MultiSelect data={regions} label="자치구" value={selectedRegions} onChange={onRegionsChange} searchable clearable />
      <div>
        <Text size="sm" fw={700} mb={8}>
          등급
        </Text>
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
      <SegmentedControl value={sort} onChange={(value) => onSortChange(value as SortMode)} data={sortOptions} />
      <Checkbox
        label="폐업 포함"
        checked={closedVisible}
        onChange={(event) => onClosedVisibleChange(event.currentTarget.checked)}
      />
      <Button variant="light" leftSection={<RotateCcw size={16} />} onClick={onReset}>
        필터 초기화
      </Button>
    </div>
  );
}

function MobileInfoPanel() {
  return (
    <div className="mobile-panel">
      <Text fw={800}>정보</Text>
      <Text size="sm" c="dimmed">
        {SOURCE_NOTICE}
      </Text>
      <Text size="sm">등급은 방문 빈도와 부서 다양성 기반 통계 신호이며 맛·품질·비위 여부를 단정하지 않습니다.</Text>
      <Button component="a" href="/legal" variant="light" leftSection={<ShieldCheck size={16} />}>
        데이터 출처
      </Button>
      <Button component="a" href="/api" variant="light" leftSection={<Code2 size={16} />}>
        API 문서
      </Button>
      <Button component="a" href="/disclaimer" variant="subtle" leftSection={<AlertTriangle size={16} />}>
        면책조항
      </Button>
    </div>
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
    <nav className="bottom-nav" aria-label="모바일 주요 메뉴">
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
      <button type="button" data-active={mode === 'info' || mode === 'detail'} onClick={() => onChange(hasSelection ? 'detail' : 'info')}>
        {hasSelection ? <Building2 size={18} aria-hidden /> : <Info size={18} aria-hidden />}
        {hasSelection ? '상세' : '정보'}
      </button>
    </nav>
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

function AdSlot() {
  if (!AD_SLOT_TEXT) return null;
  const content = (
    <>
      <span className="ad-label">후원</span>
      <span>{AD_SLOT_TEXT}</span>
    </>
  );
  if (AD_SLOT_URL) {
    return (
      <a className="ad-slot" href={AD_SLOT_URL} target="_blank" rel="noreferrer">
        {content}
      </a>
    );
  }
  return <div className="ad-slot">{content}</div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MapCanvas({
  places,
  selectedPlace,
  onSelect,
  onBlankClick,
}: {
  places: Place[];
  selectedPlace: Place | null;
  onSelect: (place: Place) => void;
  onBlankClick: () => void;
}) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const clustererRef = useRef<any>(null);
  const markersRef = useRef<MarkerEntry[]>([]);
  const onSelectRef = useRef(onSelect);
  const onBlankClickRef = useRef(onBlankClick);
  const hasFitBoundsRef = useRef(false);
  const [kakaoReady, setKakaoReady] = useState(false);
  const [kakaoFailed, setKakaoFailed] = useState(false);

  useEffect(() => {
    onSelectRef.current = onSelect;
    onBlankClickRef.current = onBlankClick;
  }, [onBlankClick, onSelect]);

  useEffect(() => {
    if (!KAKAO_JS_KEY) return;
    let cancelled = false;
    loadKakao(KAKAO_JS_KEY)
      .then(() => {
        if (!cancelled) setKakaoReady(true);
      })
      .catch(() => {
        if (!cancelled) setKakaoFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!kakaoReady || !mapRef.current || mapInstanceRef.current) return;
    const kakao = window.kakao;
    const center = new kakao.maps.LatLng(SEOUL_CENTER.latitude, SEOUL_CENTER.longitude);
    const map = new kakao.maps.Map(mapRef.current, { center, level: 8 });
    const clusterer = new kakao.maps.MarkerClusterer({
      map,
      averageCenter: true,
      minLevel: 7,
      disableClickZoom: true,
      styles: [
        {
          width: '36px',
          height: '36px',
          background: '#ef4444',
          color: '#fff',
          border: '2px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 10px 24px rgba(15,23,42,0.24)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '34px',
        },
        {
          width: '44px',
          height: '44px',
          background: '#f59e0b',
          color: '#fff',
          border: '2px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 10px 24px rgba(15,23,42,0.24)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '42px',
        },
        {
          width: '52px',
          height: '52px',
          background: '#3b82f6',
          color: '#fff',
          border: '2px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 10px 24px rgba(15,23,42,0.24)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '50px',
        },
      ],
      calculator: [10, 50],
    });
    mapInstanceRef.current = map;
    clustererRef.current = clusterer;
    kakao.maps.event.addListener(clusterer, 'clusterclick', (cluster: any) => {
      const level = Math.max(1, map.getLevel() - 2);
      map.setLevel(level, { anchor: cluster.getCenter() });
      map.panTo(cluster.getCenter());
    });
    kakao.maps.event.addListener(map, 'click', () => {
      onBlankClickRef.current();
    });
  }, [kakaoReady]);

  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current || !clustererRef.current) return;
    const kakao = window.kakao;
    const map = mapInstanceRef.current;
    const clusterer = clustererRef.current;

    clusterer.clear();
    markersRef.current.forEach(({ marker, listener }) => {
      kakao.maps.event.removeListener(marker, 'click', listener);
      marker.setMap(null);
    });
    markersRef.current = [];

    const bounds = new kakao.maps.LatLngBounds();
    const entries = places
      .filter((place) => place.latitude && place.longitude)
      .map((place) => {
        const position = new kakao.maps.LatLng(place.latitude, place.longitude);
        bounds.extend(position);
        const marker = new kakao.maps.Marker({
          position,
          title: markerAccessibleName(place),
          image: createMarkerImage(kakao, place, selectedPlace?.id === place.id),
          zIndex: selectedPlace?.id === place.id ? 30 : 10,
        });
        const listener = () => onSelectRef.current(place);
        kakao.maps.event.addListener(marker, 'click', listener);
        return { marker, place, listener };
      });

    markersRef.current = entries;
    clusterer.addMarkers(entries.map((entry) => entry.marker));
    if (entries.length > 1 && (!hasFitBoundsRef.current || places.length < 20)) {
      map.setBounds(bounds);
      hasFitBoundsRef.current = true;
    }
  }, [kakaoReady, places, selectedPlace?.id]);

  useEffect(() => {
    if (!kakaoReady) return;
    const kakao = window.kakao;
    markersRef.current.forEach(({ marker, place }) => {
      const selected = selectedPlace?.id === place.id;
      marker.setImage(createMarkerImage(kakao, place, selected));
      marker.setZIndex(selected ? 30 : 10);
      if (selected && place.latitude && place.longitude && mapInstanceRef.current) {
        mapInstanceRef.current.panTo(new kakao.maps.LatLng(place.latitude, place.longitude));
      }
    });
  }, [kakaoReady, selectedPlace?.id]);

  if (!KAKAO_JS_KEY || kakaoFailed) {
    return <FallbackMap places={places} selectedId={selectedPlace?.id} onSelect={onSelect} />;
  }

  return (
    <>
      <div className="kakao-map" ref={mapRef} aria-label="카카오 지도" />
      {!kakaoReady ? (
        <div className="map-status" role="status">
          <Loader size="sm" />
          <Text size="sm">카카오 지도를 불러오는 중입니다.</Text>
        </div>
      ) : null}
    </>
  );
}

function FallbackMap({
  places,
  selectedId,
  onSelect,
}: {
  places: Place[];
  selectedId?: string;
  onSelect: (place: Place) => void;
}) {
  const [expandedRegion, setExpandedRegion] = useState<string | null>(null);
  const located = places.filter((place) => place.latitude && place.longitude);
  const clusters = useMemo(() => {
    const grouped = new Map<string, Place[]>();
    located.forEach((place) => {
      const region = place.road_address_part ?? '서울';
      grouped.set(region, [...(grouped.get(region) ?? []), place]);
    });
    return Array.from(grouped.entries()).map(([region, items]) => ({
      region,
      items,
      latitude: average(items.map((item) => item.latitude ?? SEOUL_CENTER.latitude)),
      longitude: average(items.map((item) => item.longitude ?? SEOUL_CENTER.longitude)),
    }));
  }, [located]);

  const markerPlaces = expandedRegion
    ? located.filter((place) => (place.road_address_part ?? '서울') === expandedRegion)
    : located.length > 30
      ? []
      : located;

  return (
    <div className="fallback-map" role="application" aria-label="지도 대체 화면">
      {!expandedRegion && located.length > 30
        ? clusters.map((cluster) => (
            <button
              className="fallback-cluster"
              key={cluster.region}
              type="button"
              style={positionStyle(cluster.latitude, cluster.longitude)}
              onClick={() => setExpandedRegion(cluster.region)}
              aria-label={`${shortRegionLabel(cluster.region)} 식당 ${cluster.items.length}곳 확대`}
            >
              {cluster.items.length}
            </button>
          ))
        : null}
      {expandedRegion ? (
        <Button className="fallback-back" size="xs" variant="light" leftSection={<Layers size={14} />} onClick={() => setExpandedRegion(null)}>
          클러스터로 보기
        </Button>
      ) : null}
      {markerPlaces.map((place) => (
        <button
          className={`map-marker grade-${gradeClass(place.grade)}`}
          data-active={place.id === selectedId}
          key={place.id}
          type="button"
          style={positionStyle(place.latitude ?? SEOUL_CENTER.latitude, place.longitude ?? SEOUL_CENTER.longitude)}
          onClick={() => onSelect(place)}
          aria-label={markerAccessibleName(place)}
        >
          {markerLabel(place.grade)}
        </button>
      ))}
    </div>
  );
}

function StaticPage({ path }: { path: string }) {
  const page = staticPageContent(path);
  const PageIcon = page.icon;
  return (
    <AppShell header={{ height: 64 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="lg" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <PageIcon size={21} aria-hidden />
            <Title order={1}>{page.title}</Title>
          </Group>
          <Button component="a" href="/" variant="subtle" leftSection={<MapPin size={16} />}>
            지도
          </Button>
        </Group>
      </AppShell.Header>
      <AppShell.Main className="legal-main">
        <article className="legal-page">
          <Text c="dimmed">{page.lead}</Text>
          {page.sections.map((section) => (
            <section key={section.title} className="legal-section">
              <Title order={2}>{section.title}</Title>
              {section.lines.map((line) => (
                <Text key={line}>{line}</Text>
              ))}
              {section.links ? (
                <Group gap="md" mt="sm">
                  {section.links.map((link) => (
                    <Button key={link.href} component="a" href={link.href} variant="light">
                      {link.label}
                    </Button>
                  ))}
                </Group>
              ) : null}
            </section>
          ))}
        </article>
        <footer className="site-footer static-footer">
          <span>공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외 51개 기관</span>
          <span>운영: 이원영/WonYoungLee · wylee0806@naver.com · 010-7133-0806 · 경기도 성남시 분당구 수내로 39</span>
          <nav aria-label="문서 링크">
            <Anchor href="/about">서비스 소개</Anchor>
            <Anchor href="/terms">이용약관</Anchor>
            <Anchor href="/privacy">개인정보처리방침</Anchor>
            <Anchor href="/disclaimer">면책조항</Anchor>
            <Anchor href="/legal">데이터 출처</Anchor>
            <Anchor href="/api">API 문서</Anchor>
          </nav>
        </footer>
      </AppShell.Main>
    </AppShell>
  );
}

function staticPageContent(path: string) {
  if (path === '/privacy') {
    return {
      title: '개인정보처리방침',
      icon: ShieldCheck,
      lead: '공무원맵은 회원가입 없이 이용할 수 있으며, 신고 처리에 필요한 최소 정보만 사용합니다.',
      sections: [
        {
          title: '수집 항목',
          lines: [
            '폐업 신고 중복 방지를 위한 익명 브라우저 식별자, 정보 수정·삭제 요청 시 사용자가 입력한 이메일을 처리합니다.',
            '방문 기록 데이터는 법령에 따라 공개된 업무추진비 집행내역을 가공한 것이며, 일반직 공무원 실명은 적재 단계에서 마스킹합니다.',
          ],
        },
        {
          title: '이용 목적과 보관',
          lines: [
            '익명 식별자는 중복 신고 차단에 사용하며 90일 단위 삭제를 원칙으로 합니다.',
            '이메일은 요청 회신과 분쟁 대응에만 사용하고, 응답 완료 후 30일 보관을 원칙으로 합니다.',
          ],
        },
        {
          title: '처리 위탁',
          lines: [
            '서비스 운영에는 Vercel, Neon, Cloudflare R2, Resend가 사용될 수 있습니다.',
            '개인정보 보호 책임자는 이원영/WonYoungLee이며 연락처는 wylee0806@naver.com입니다.',
          ],
        },
      ],
    };
  }
  if (path === '/terms') {
    return {
      title: '이용약관',
      icon: FileText,
      lead: '공무원맵은 공공 공개자료를 시민이 쉽게 탐색할 수 있도록 제공하는 무료 정보 서비스입니다.',
      sections: [
        {
          title: '서비스 제공',
          lines: [
            '데이터는 원문 공개자료, 자동 추출, 카카오 로컬 매칭 결과를 바탕으로 제공되며 정확성을 보증하지 않습니다.',
            '사용자는 데이터 재이용 시 원 출처와 공공누리 제1유형 조건을 함께 확인해야 합니다.',
          ],
        },
        {
          title: '금지 행위',
          lines: [
            '공무원 개인의 식습관·성향을 추론하거나 부정행위를 단정하는 방식의 이용을 금지합니다.',
            '서비스 안정성을 해치는 자동화 요청, 권리침해 목적의 재게시, 출처 삭제 재배포를 금지합니다.',
          ],
        },
        {
          title: '분쟁',
          lines: [
            '정보 수정·삭제 요청은 접수 즉시 임시 비공개 처리하고 72시간 내 검토합니다.',
            '분쟁은 대한민국 법령에 따르며 운영자 주소지 관할 법원을 1심 관할로 합니다.',
          ],
        },
      ],
    };
  }
  if (path === '/disclaimer') {
    return {
      title: '면책조항',
      icon: AlertTriangle,
      lead: '등급은 방문 빈도와 부서 다양성에 따른 통계 신호이며 맛·품질·비위 여부를 단정하지 않습니다.',
      sections: [
        {
          title: '데이터 성격',
          lines: [
            '본 서비스는 정보공개법과 업무추진비 공개기준에 따라 공개된 자료를 가공·재공개합니다.',
            '식당의 개·폐업, 영업시간, 가격은 최신 상태와 다를 수 있으므로 방문 전 별도 확인이 필요합니다.',
          ],
        },
        {
          title: '표현의 한계',
          lines: [
            '업무추진비는 법령상 허용된 공무 집행의 한 형태이며, 본 서비스는 부정행위나 비위를 암시하지 않습니다.',
            '사용자 댓글·평점·후기는 v1에서 제공하지 않습니다.',
          ],
        },
        {
          title: '정정 요청',
          lines: [
            '정보 수정·삭제 요청은 식당 상세 패널 또는 운영자 이메일로 접수할 수 있습니다.',
            '요청이 접수되면 해당 정보는 자동으로 임시 비공개 처리됩니다.',
          ],
        },
      ],
    };
  }
  if (path === '/legal') {
    return {
      title: '데이터 출처와 법적 근거',
      icon: ShieldCheck,
      lead: '공무원맵은 법령상 공개 대상인 업무추진비 집행내역과 공공누리 제1유형 자료를 사용합니다.',
      sections: [
        {
          title: '출처 표시',
          lines: [
            '주요 출처는 서울특별시 정보소통광장, 서울시의회, 25개 자치구청, 25개 자치구의회 공개 게시판입니다.',
            '공공누리 제1유형 조건에 따라 출처를 표시하고, 서비스 전 페이지와 API 문서에 데이터 출처를 명시합니다.',
          ],
        },
        {
          title: '표기 정책',
          lines: [
            '선거직 고위공무원은 실명과 직급 표시가 가능하지만, 임명직과 5급 이하 일반직은 부서·직급 중심으로 마스킹합니다.',
            '민간인 동석자는 원칙적으로 마스킹하며, 식당명·주소·일자·금액은 원본 공개 항목으로 표시합니다.',
          ],
        },
        {
          title: '운영자',
          lines: [
            '운영자: 이원영/WonYoungLee',
            '이메일: wylee0806@naver.com · 연락처: 010-7133-0806 · 주소: 경기도 성남시 분당구 수내로 39',
            '사업자등록번호: 해당 없음, 개인 운영',
          ],
        },
      ],
    };
  }
  if (path === '/api') {
    return {
      title: 'API 문서',
      icon: Code2,
      lead: '공무원맵은 지도 화면과 동일한 공개 데이터를 REST API와 OpenAPI 3.1 스펙으로 제공합니다.',
      sections: [
        {
          title: '주요 엔드포인트',
          lines: [
            'GET /api/v1/places: bbox, grade, limit 파라미터로 식당 목록을 조회합니다.',
            'GET /api/v1/places/search: 검색어, 자치구, 등급, 정렬 기반 UI 목록을 조회합니다.',
            'GET /api/v1/regions: 자치구별 식당 수와 지도 중심 좌표를 조회합니다.',
            'GET /api/v1/places/{id}/visits: 원문 링크가 포함된 방문 기록을 조회합니다.',
          ],
          links: [
            { label: 'OpenAPI JSON', href: '/openapi.json' },
            { label: 'llms.txt', href: '/llms.txt' },
          ],
        },
        {
          title: '이용 조건',
          lines: [
            'GET API는 공개 캐시가 적용되며, 데이터 인용 시 공무원맵과 원 공공자료 출처를 함께 표시해야 합니다.',
            '등급은 통계 신호이므로 식당 평가나 공무원 비위 판단 근거로 단정해서 사용할 수 없습니다.',
          ],
        },
      ],
    };
  }
  return {
    title: '서비스 소개',
    icon: Info,
    lead: '공무원맵은 서울 52개 기관의 업무추진비 집행내역에서 식당 방문 신호를 추출해 지도에 표시합니다.',
    sections: [
      {
        title: '집계 현황',
        lines: [
          '2026년 5월 25일 기준 52개 기관 중 51개 기관이 지도 집계에 반영되어 있습니다.',
          '중랑구청은 공식 PDF에 장소·가맹점 열이 없어 보조 출처 확보 전까지 지도 집계에서 제외합니다.',
        ],
      },
      {
        title: '등급 산식',
        lines: [
          '점수는 방문 횟수와 고유 부서 수를 함께 반영합니다.',
          '자치구별 백분위 기준으로 강추, 추천, 중립, 신규 라벨을 부여합니다.',
        ],
      },
      {
        title: '서비스 원칙',
        lines: [
          '공식 공개자료만 사용하며 사용자 댓글·평점·후기는 받지 않습니다.',
          '공무원의 부정행위나 식당의 맛을 단정하지 않고, 출처 확인 가능한 방문 빈도 신호만 제공합니다.',
        ],
      },
    ],
  };
}

function parseQueryState(search = window.location.search): QueryState {
  const params = new URLSearchParams(search);
  return normalizeQueryState({
    q: params.get('q') ?? '',
    region: splitList(params.get('region')),
    grade: parseGrades(params.get('grade')),
    sort: parseSort(params.get('sort')),
    placeId: params.get('place'),
  });
}

function initialMobileMode(state: QueryState): MobileMode {
  if (state.placeId) return 'detail';
  if (state.q || state.region.length) return 'list';
  return 'map';
}

function normalizeQueryState(state: QueryState): QueryState {
  return {
    q: state.q.trim(),
    region: Array.from(new Set(state.region.filter(Boolean))),
    grade: state.grade.length ? Array.from(new Set(state.grade)) : defaultGrades,
    sort: parseSort(state.sort),
    placeId: state.placeId || null,
  };
}

function parseGrades(raw: string | null): Grade[] {
  const values = splitList(raw).filter((value): value is Grade => gradeOptions.includes(value as Grade));
  return values.length ? values : defaultGrades;
}

function splitList(raw: string | null) {
  return raw
    ? raw
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean)
    : [];
}

function parseSort(raw: string | null | SortMode): SortMode {
  return raw === 'recent' || raw === 'visits' || raw === 'score' ? raw : 'score';
}

function serializeQueryState(state: QueryState) {
  const params = new URLSearchParams();
  if (state.q) params.set('q', state.q);
  if (state.region.length) params.set('region', state.region.join(','));
  if (state.grade.length && state.grade.join(',') !== defaultGrades.join(',')) params.set('grade', state.grade.join(','));
  if (state.sort !== 'score') params.set('sort', state.sort);
  if (state.placeId) params.set('place', state.placeId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

function pushUrlState(state: QueryState) {
  window.history.pushState(null, '', `${window.location.pathname}${serializeQueryState(state)}`);
}

function replaceUrlState(state: QueryState) {
  window.history.replaceState(null, '', `${window.location.pathname}${serializeQueryState(state)}`);
}

function sortPlaces(places: Place[], sort: SortMode) {
  return [...places].sort((a, b) => {
    if (sort === 'recent') return compareDates(b.last_visit_at, a.last_visit_at) || Number(b.score ?? 0) - Number(a.score ?? 0);
    if (sort === 'visits') {
      return (
        Number(b.visit_count_12m ?? 0) - Number(a.visit_count_12m ?? 0) ||
        Number(b.unique_department_count_12m ?? 0) - Number(a.unique_department_count_12m ?? 0)
      );
    }
    return Number(b.score ?? 0) - Number(a.score ?? 0) || compareDates(b.last_visit_at, a.last_visit_at);
  });
}

function compareDates(a: string | null, b: string | null) {
  return (a ? Date.parse(a) : 0) - (b ? Date.parse(b) : 0);
}

function formatDate(value: string | null | undefined) {
  if (!value) return null;
  const [date] = value.split('T');
  const parts = date.split('-');
  if (parts.length !== 3) return value;
  return `${parts[0]}.${parts[1]}.${parts[2]}`;
}

function gradeLabel(grade: string) {
  if (grade === '★★★') return '강추';
  if (grade === '★★') return '추천';
  if (grade === '★') return '중립';
  return '신규';
}

function markerLabel(grade: string) {
  if (grade === '★★★') return '3★';
  if (grade === '★★') return '2★';
  if (grade === '★') return '1★';
  return 'NEW';
}

function gradeClass(grade: string) {
  if (grade === '★★★') return 'top';
  if (grade === '★★') return 'good';
  if (grade === '★') return 'neutral';
  return 'new';
}

function markerAccessibleName(place: Place) {
  return `${gradeLabel(place.grade)} 등급, ${place.name}, ${shortRegionLabel(place.road_address_part ?? '서울')}`;
}

function shortRegionLabel(region: string) {
  return region.replace(/^서울\s*/, '') || region;
}

function positionStyle(latitude: number, longitude: number) {
  const left = ((longitude - 126.734) / (127.269 - 126.734)) * 100;
  const top = (1 - (latitude - 37.413) / (37.715 - 37.413)) * 100;
  return {
    left: `${Math.min(96, Math.max(4, left))}%`,
    top: `${Math.min(92, Math.max(8, top))}%`,
  };
}

function average(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function createMarkerImage(kakao: any, place: Place, selected: boolean) {
  const size = markerSize(place.grade) + (selected ? 4 : 0);
  const color = gradeColor(place.grade);
  const opacity = place.is_closed ? 0.35 : 1;
  const label = markerLabel(place.grade);
  const svg = encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size + 6}" viewBox="0 0 ${size} ${size + 6}">
      <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 2}" fill="${color}" fill-opacity="${opacity}" stroke="#fff" stroke-width="2"/>
      ${selected ? `<circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 1}" fill="none" stroke="#172033" stroke-width="3"/>` : ''}
      <text x="50%" y="${size / 2 + 4}" text-anchor="middle" font-family="Arial, sans-serif" font-weight="800" font-size="${label === 'NEW' ? 9 : 10}" fill="#fff">${label}</text>
    </svg>
  `);
  return new kakao.maps.MarkerImage(`data:image/svg+xml;charset=utf-8,${svg}`, new kakao.maps.Size(size, size + 6), {
    offset: new kakao.maps.Point(size / 2, size + 2),
  });
}

function markerSize(grade: Grade) {
  if (grade === '★★★') return 34;
  if (grade === '★★') return 30;
  return 26;
}

function gradeColor(grade: Grade) {
  if (grade === '★★★') return '#ef4444';
  if (grade === '★★') return '#f59e0b';
  if (grade === '★') return '#6b7280';
  return '#3b82f6';
}

function browserFingerprint() {
  const key = 'public-officer-map-fp';
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const next = crypto.randomUUID();
  window.localStorage.setItem(key, next);
  return next;
}

function loadKakao(appKey: string) {
  if (window.kakao?.maps?.MarkerClusterer) {
    return Promise.resolve();
  }
  return new Promise<void>((resolve, reject) => {
    let settled = false;
    const timeout = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(new Error('kakao map timeout'));
    }, 4500);
    const done = () => {
      if (settled) return;
      try {
        window.kakao.maps.load(() => {
          if (settled) return;
          settled = true;
          window.clearTimeout(timeout);
          resolve();
        });
      } catch {
        settled = true;
        window.clearTimeout(timeout);
        reject(new Error('kakao map failed'));
      }
    };
    const failed = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeout);
      reject(new Error('kakao map failed'));
    };
    const existing = document.querySelector<HTMLScriptElement>('script[data-kakao-map]');
    if (existing) {
      existing.addEventListener('load', done);
      existing.addEventListener('error', failed);
      return;
    }
    const script = document.createElement('script');
    script.dataset.kakaoMap = 'true';
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&libraries=clusterer&autoload=false`;
    script.async = true;
    script.onload = done;
    script.onerror = failed;
    document.head.appendChild(script);
  });
}

declare global {
  interface Window {
    kakao: any;
  }
}
