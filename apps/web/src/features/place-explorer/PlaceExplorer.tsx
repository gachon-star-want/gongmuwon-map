import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Button,
  Modal,
  Radio,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  AlertTriangle,
  FileText,
  RefreshCw,
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
import { shortRegionLabel, sortPlaces } from './format';
import {
  allGrades,
  defaultGrades,
  isDefaultGradeFilter,
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
import { AuthModal } from '../auth/AuthModal';
import type { AuthStateChangeDetail, CurrentUser } from '../auth/authApi';
import { AUTH_STATE_CHANGE_EVENT, getCurrentUser, logout } from '../auth/authApi';
import { TurnstileWidget } from '../../shared/TurnstileWidget';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useReportFlow } from './hooks/useReportFlow';
import { MapSearchBar } from './panels/MapSearchBar';
import { MapFilterBar } from './panels/MapFilterBar';
import { BottomNav } from './panels/BottomNav';
import { classifyFoodCategory } from './foodCategories';
import './styles.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SEARCH_DEBOUNCE_MS = 600;

export function PlaceExplorer() {
  const initialQuery = useMemo(() => {
    const parsed = parseQueryState();
    return { ...parsed, placeId: null };
  }, []);
  const [queryState, setQueryState] = useState<PlaceQueryState>(() => initialQuery);
  const [searchDraft, setSearchDraft] = useState(() => initialQuery.q);
  const [places, setPlaces] = useState<Place[]>([]);
  const [searchPlaces, setSearchPlaces] = useState<Place[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [lastPlace, setLastPlace] = useState<Place | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [reactions, setReactions] = useState<PlaceReactionSummary | null>(null);
  const [reactionPending, setReactionPending] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [regionLoading, setRegionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [closedVisible, setClosedVisible] = useState(false);
  const [desktopListOpen, setDesktopListOpen] = useState(false);
  const [mobileMode, setMobileMode] = useState<MobileMode>(() => initialMobileMode(initialQuery));
  const [sheetSize, setSheetSize] = useState<SheetSize>('mid');
  const [authOpened, auth] = useDisclosure(false);
  const [mapBbox, setMapBbox] = useState<[number, number, number, number] | null>(null);
  const bboxDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let changed = false;
    if (params.has('place')) {
      params.delete('place');
      changed = true;
    }

    const parsedState = parseQueryState(window.location.search, window.location.pathname);
    const serializedQuery = serializeQueryState(parsedState);
    const currentPath = resolveExplorerPathname(window.location.pathname, parsedState);
    const targetUrl = `${currentPath}${serializedQuery}`;
    const currentUrl = `${window.location.pathname}${window.location.search}`;

    if (currentUrl !== targetUrl || changed) {
      window.history.replaceState(null, '', targetUrl);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (bboxDebounceRef.current) clearTimeout(bboxDebounceRef.current);
    };
  }, []);

  const regionOptions = useMemo(() => {
    const fromApi = regions.map((region) => ({ label: region.label, value: region.region }));
    if (fromApi.length) return fromApi;
    return Array.from(new Set(places.map((place) => place.road_address_part).filter(Boolean) as string[]))
      .sort()
      .map((region) => ({ label: shortRegionLabel(region), value: region }));
  }, [places, regions]);

  // 1글자 q 단독 검색은 remote search를 타지 않고 로컬 places 필터링으로 처리
  const hasActiveSearchFilter = Boolean(
    queryState.q.trim().length >= 2 || queryState.region.length > 0
  );
  const activeResultPlaces = useMemo(
    () => hasActiveSearchFilter ? searchPlaces : places,
    [hasActiveSearchFilter, searchPlaces, places],
  );

  const visibleResultPlaces = useMemo(() => {
    const normalizedQuery = queryState.q.trim().toLowerCase();
    return activeResultPlaces.filter((place) => {
      if (!closedVisible && place.is_closed) return false;
      if (!queryState.grade.includes(place.grade)) return false;
      if (queryState.region.length && (!place.road_address_part || !queryState.region.includes(place.road_address_part))) return false;
      if (normalizedQuery) {
        const foodCategory = classifyFoodCategory(place);
        const haystack = `${place.name} ${place.road_address ?? ''} ${place.road_address_part ?? ''} ${place.category ?? ''} ${foodCategory.key} ${foodCategory.label}`.toLowerCase();
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
    if (!hasActiveSearchFilter && !closedVisible && isDefaultGradeFilter(queryState.grade) && !queryState.q) return `${count}곳`;
    const parts = [];
    if (queryState.q) parts.push(`"${queryState.q}"`);
    if (queryState.region.length) parts.push(`${queryState.region.length}개 자치구`);
    if (!isDefaultGradeFilter(queryState.grade)) parts.push(queryState.grade.join(',') === allGrades.join(',') ? '전체 등급' : '등급 필터');
    if (closedVisible) parts.push('폐업 포함');
    return `${parts.join(' · ')} 결과 ${count}곳`;
  }, [closedVisible, hasActiveSearchFilter, listedPlaces.length, queryState.grade, queryState.q, queryState.region.length]);
  const listError = hasActiveSearchFilter ? searchError : null;
  const listLoading = hasActiveSearchFilter ? searchLoading : false;
  const hasActiveFilter = hasActiveSearchFilter || closedVisible || !isDefaultGradeFilter(queryState.grade);

  const {
    isClosureModalOpen,
    setIsClosureModalOpen,
    isTakedownModalOpen,
    setIsTakedownModalOpen,
    closureReason,
    setClosureReason,
    reportForm,
    setReportForm,
    closureState,
    requestState,
    closureTurnstileToken,
    setClosureTurnstileToken,
    requestTurnstileToken,
    setRequestTurnstileToken,
    closureTurnstileReset,
    requestTurnstileReset,
    submitClosureReport: submitClosureReportForm,
    submitTakedownRequestForm,
    resetTakedownForm,
    resetClosureForm,
  } = useReportFlow({
    selectedPlace,
    onAfterClosureReport: async () => {
      await loadPlaces();
      await loadSearchPlaces(new AbortController());
    },
    onAfterTakedownRequest: (placeId) => {
      setPlaces((current) => current.filter((place) => place.id !== placeId));
      setSearchPlaces((current) => current.filter((place) => place.id !== placeId));
      clearSelected('replace');
    },
  });

  const isModalOpen = isTakedownModalOpen || isClosureModalOpen || authOpened;

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
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timeout);
  }, [searchDraft]);

  useEffect(() => {
    const hasKakaoKey = Boolean(import.meta.env.VITE_KAKAO_JS_KEY);
    if (hasKakaoKey && !mapBbox) return;

    const controller = new AbortController();
    void loadPlaces(controller.signal);
    return () => controller.abort();
  }, [queryState.grade, mapBbox]);

  useEffect(() => {
    void loadRegions();
  }, []);

  useEffect(() => {
    void getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));

    const onAuthStateChange = (event: Event) => {
      setCurrentUser((event as CustomEvent<AuthStateChangeDetail>).detail.user);
    };
    window.addEventListener(AUTH_STATE_CHANGE_EVENT, onAuthStateChange);
    return () => window.removeEventListener(AUTH_STATE_CHANGE_EVENT, onAuthStateChange);
  }, []);

  useEffect(() => {
    if (!hasActiveSearchFilter) {
      setSearchPlaces([]);
      return;
    }
    const controller = new AbortController();
    void loadSearchPlaces(controller);
    return () => controller.abort();
  }, [hasActiveSearchFilter, queryState.grade, queryState.q, queryState.region, queryState.sort]);

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
    setLastPlace(selectedPlace);
    void loadVisits(selectedPlace.id);
    void loadPlaceReactions(selectedPlace.id);
  }, [selectedPlace]);

  useKeyboardShortcuts({
    isModalOpen,
    hasSelection: Boolean(selectedPlace),
    isDesktopListOpen: desktopListOpen,
    isMobilePanelOpen: mobileMode !== 'map',
    onClearSelection: () => clearSelected(),
    onCloseDesktopList: () => setDesktopListOpen(false),
    onCloseMobilePanel: () => setMobileMode('map'),
  });

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

  async function loadPlaces(signal?: AbortSignal) {
    setError(null);
    try {
      const result = await loadPlacesApi({ grade: queryState.grade }, mapBbox ?? undefined, signal);
      setPlaces(result);
    } catch (err) {
      if ((err as DOMException).name !== 'AbortError') {
        setError('데이터를 불러오지 못했습니다.');
      }
    }
  }

  async function loadSearchPlaces(controller: AbortController) {
    setSearchLoading(true);
    setSearchError(null);
    setSearchPlaces([]);
    try {
      // 1글자 이하의 q는 DB 쿼리 부하 최소화를 위해 remote API 요청 파라미터에서 제외하고,
      // 받아온 자치구 등 결과 리스트에서 로컬 필터링하도록 우회 처리
      const apiQuery = {
        ...queryState,
        q: queryState.q.trim().length >= 2 ? queryState.q : '',
      };
      const data = await searchPlacesApi(apiQuery, controller.signal);
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
    if (mode === 'filter') {
      setSheetSize('full');
    } else {
      setSheetSize('mid');
    }
  }

  const mapOverlays = (
    <>
      <div className="map-search-wrap">
        <MapSearchBar value={searchDraft} onChange={setSearchDraft} />
        <MapFilterBar
          regions={regionOptions}
          selectedRegions={queryState.region}
          onRegionsChange={(region) => {
            updateQueryState({ region });
          }}
          selectedGrades={queryState.grade}
          onGradesChange={(grade) => updateQueryState({ grade })}
          sort={queryState.sort}
          onSortChange={(sort) => updateQueryState({ sort })}
          closedVisible={closedVisible}
          onClosedVisibleChange={setClosedVisible}
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
      </div>

      <MapCanvas
        places={visibleMapPlaces}
        selectedPlace={selectedPlace}
        onSelect={selectPlace}
        onBlankClick={() => {
          if (selectedPlace) clearSelected();
        }}
        onBoundsChange={(bbox) => {
          if (bboxDebounceRef.current) clearTimeout(bboxDebounceRef.current);
          bboxDebounceRef.current = setTimeout(() => {
            setMapBbox(bbox);
          }, 400);
        }}
        desktopListOpen={desktopListOpen}
        onUserLocationChange={setUserLocation}
      />

      {error ? (
        <div className="map-status map-status-error" role="alert">
          <Text size="sm">{error}</Text>
          <Button size="xs" variant="light" leftSection={<RefreshCw size={14} />} onClick={() => void loadPlaces()}>
            다시 시도
          </Button>
        </div>
      ) : null}

      <aside className={`detail-drawer desktop-layer ${selectedPlace ? 'active' : ''} ${desktopListOpen ? 'list-open' : ''}`} aria-label="식당 상세">
        {lastPlace ? (
          <PlaceDetails
            place={lastPlace}
            visits={visits}
            onClose={() => clearSelected()}
            onReport={() => setIsTakedownModalOpen(true)}
            onClosureReport={() => setIsClosureModalOpen(true)}
            userLocation={userLocation}
          />
        ) : null}
      </aside>

      <BottomSheet
        mode={mobileMode}
        size={sheetSize}
        selectedPlace={selectedPlace}
        places={listedPlaces}
        selectedId={selectedPlace?.id}
        visits={visits}
        loading={listLoading}
        error={listError}
        resultLabel={resultLabel}
        hasActiveFilter={hasActiveFilter}
        regions={regionOptions}
        selectedRegions={queryState.region}
        selectedGrades={queryState.grade}
        sort={queryState.sort}
        closedVisible={closedVisible}
        userLocation={userLocation}
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
        onReport={() => setIsTakedownModalOpen(true)}
        onClosureReport={() => setIsClosureModalOpen(true)}
        hidden={isModalOpen}
      />

      {!isModalOpen ? (
        <BottomNav mode={mobileMode} onChange={changeMobileMode} hasSelection={Boolean(selectedPlace)} />
      ) : null}
    </>
  );

  return (
    <div className="map-area-content">
      {mapOverlays}

      /* desktop list sheet removed */

      {mobileMode === 'filter' ? (
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
      ) : null}

      <AuthModal opened={authOpened} onClose={auth.close} onAuthenticated={setCurrentUser} />

      <Modal
        opened={isTakedownModalOpen}
        onClose={() => {
          resetTakedownForm();
          setIsTakedownModalOpen(false);
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
          <Radio.Group
            label="사유"
            value={reportForm.category}
            onChange={(val) => setReportForm((prev) => ({ ...prev, category: val }))}
          >
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
            value={reportForm.reason}
            onChange={(event) => setReportForm((prev) => ({ ...prev, reason: event.currentTarget.value }))}
          />
          <TextInput
            label="이메일"
            placeholder="회신 받을 주소"
            required
            value={reportForm.email}
            onChange={(event) => setReportForm((prev) => ({ ...prev, email: event.currentTarget.value }))}
          />
          <TurnstileWidget
            action="takedown_request"
            resetSignal={`${selectedPlace?.id ?? 'none'}-${requestTurnstileReset}`}
            onTokenChange={setRequestTurnstileToken}
          />
          <Button
            leftSection={<FileText size={16} />}
            loading={requestState === 'submitting'}
            disabled={!selectedPlace || reportForm.reason.trim().length < 50 || !EMAIL_PATTERN.test(reportForm.email.trim()) || !requestTurnstileToken}
            onClick={() => void submitTakedownRequestForm()}
          >
            접수
          </Button>
          {requestState === 'done' ? <Text size="sm">접수되었습니다. 필요한 경우 임시 비공개 처리 후 72시간 내 검토합니다.</Text> : null}
          {requestState === 'error' ? (
            <Text size="sm" c="red">
              접수에 실패했습니다.
            </Text>
          ) : null}
        </Stack>
      </Modal>

      <Modal
        opened={isClosureModalOpen}
        onClose={() => {
          resetClosureForm();
          setIsClosureModalOpen(false);
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
          <TurnstileWidget
            action="closure_report"
            resetSignal={`${selectedPlace?.id ?? 'none'}-${closureTurnstileReset}`}
            onTokenChange={setClosureTurnstileToken}
          />
          <Button
            leftSection={<AlertTriangle size={16} />}
            loading={closureState === 'submitting'}
            disabled={!selectedPlace || !closureTurnstileToken}
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
    </div>
  );
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
