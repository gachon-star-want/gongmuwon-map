import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActionIcon,
  AppShell,
  Badge,
  Button,
  Checkbox,
  Group,
  Loader,
  Modal,
  MultiSelect,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { AlertTriangle, Building2, Info, MapPin, RefreshCw, Search, X } from 'lucide-react';

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
  grade: '★★★' | '★★' | '★' | '✦';
  last_visit_at: string | null;
  visit_count_12m: number | null;
  unique_department_count_12m: number | null;
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

const SEOUL_BBOX = '37.413,126.734,37.715,127.269';
const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;
const gradeOptions = ['★★★', '★★', '✦', '★'] as const;

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

export function App() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedGrades, setSelectedGrades] = useState<string[]>(['★★★', '★★', '✦']);
  const [closedVisible, setClosedVisible] = useState(false);
  const [panelMode, setPanelMode] = useState('details');
  const [reportOpened, report] = useDisclosure(false);
  const [closureOpened, closure] = useDisclosure(false);
  const [closureState, setClosureState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');

  const regions = useMemo(
    () =>
      Array.from(new Set(places.map((place) => place.road_address_part).filter(Boolean) as string[]))
        .sort()
        .map((region) => ({ label: region.replace('서울 ', ''), value: region })),
    [places],
  );

  const filteredPlaces = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return places.filter((place) => {
      if (!closedVisible && place.is_closed) return false;
      if (selectedRegions.length && (!place.road_address_part || !selectedRegions.includes(place.road_address_part))) {
        return false;
      }
      if (selectedGrades.length && !selectedGrades.includes(place.grade)) return false;
      if (normalizedQuery) {
        const haystack = `${place.name} ${place.road_address ?? ''} ${place.category ?? ''}`.toLowerCase();
        if (!haystack.includes(normalizedQuery)) return false;
      }
      return true;
    });
  }, [closedVisible, places, query, selectedGrades, selectedRegions]);

  useEffect(() => {
    void loadPlaces();
  }, []);

  useEffect(() => {
    if (!selectedPlace) {
      setVisits([]);
      return;
    }
    void loadVisits(selectedPlace.id);
  }, [selectedPlace]);

  async function loadPlaces() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(apiUrl(`/api/v1/places?bbox=${SEOUL_BBOX}&limit=500`));
      if (!response.ok) throw new Error(`places ${response.status}`);
      const data = (await response.json()) as Place[];
      setPlaces(data);
      setSelectedPlace((current) => current ?? data[0] ?? null);
    } catch {
      setError('데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
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

  return (
    <AppShell header={{ height: 64 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="lg" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <MapPin size={22} aria-hidden />
            <Title order={1}>공무원맵</Title>
            <Badge variant="light" color="gray">
              서울
            </Badge>
          </Group>
          <Group gap="xs" wrap="nowrap">
            <ActionIcon variant="subtle" aria-label="새로고침" onClick={() => void loadPlaces()}>
              <RefreshCw size={18} />
            </ActionIcon>
            <ActionIcon variant="subtle" aria-label="정보">
              <Info size={18} />
            </ActionIcon>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Main className="app-main">
        <aside className="control-panel">
          <Stack gap="md">
            <TextInput
              leftSection={<Search size={16} />}
              placeholder="식당명, 주소, 분류"
              value={query}
              onChange={(event) => setQuery(event.currentTarget.value)}
              rightSection={
                query ? (
                  <ActionIcon variant="subtle" aria-label="검색 지우기" onClick={() => setQuery('')}>
                    <X size={14} />
                  </ActionIcon>
                ) : null
              }
            />
            <MultiSelect
              data={regions}
              placeholder="자치구"
              value={selectedRegions}
              onChange={setSelectedRegions}
              searchable
              clearable
              maxDropdownHeight={260}
            />
            <div className="grade-filter" aria-label="등급 필터">
              {gradeOptions.map((grade) => (
                <Checkbox
                  key={grade}
                  label={gradeLabel(grade)}
                  checked={selectedGrades.includes(grade)}
                  onChange={(event) =>
                    setSelectedGrades((current) =>
                      event.currentTarget.checked
                        ? [...current, grade]
                        : current.filter((item) => item !== grade),
                    )
                  }
                />
              ))}
            </div>
            <Checkbox
              label="폐업 포함"
              checked={closedVisible}
              onChange={(event) => setClosedVisible(event.currentTarget.checked)}
            />
            <SegmentedControl
              value={panelMode}
              onChange={setPanelMode}
              data={[
                { label: '상세', value: 'details' },
                { label: '목록', value: 'list' },
              ]}
            />
          </Stack>
        </aside>

        <section className="map-surface" aria-label="공무원맵 지도">
          {loading ? (
            <div className="center-state">
              <Loader />
            </div>
          ) : error ? (
            <div className="center-state">
              <Text>{error}</Text>
              <Button variant="light" leftSection={<RefreshCw size={16} />} onClick={() => void loadPlaces()}>
                다시 시도
              </Button>
            </div>
          ) : (
            <MapCanvas places={filteredPlaces} selectedPlace={selectedPlace} onSelect={setSelectedPlace} />
          )}
        </section>

        <aside className="detail-panel" data-mode={panelMode}>
          {panelMode === 'list' ? (
            <PlaceList places={filteredPlaces} selectedId={selectedPlace?.id} onSelect={setSelectedPlace} />
          ) : (
            <PlaceDetails
              place={selectedPlace}
              visits={visits}
              onReport={report.open}
              onClosureReport={closure.open}
            />
          )}
        </aside>
      </AppShell.Main>

      <Modal opened={reportOpened} onClose={report.close} title="정보 수정·삭제 요청" centered>
        <Stack>
          <Text size="sm" c="dimmed">
            접수 즉시 임시 비공개 처리 후 72시간 내 검토합니다.
          </Text>
          <TextInput label="식당" value={selectedPlace?.name ?? ''} readOnly />
          <TextInput label="이메일" placeholder="회신 받을 주소" />
          <Button leftSection={<AlertTriangle size={16} />} onClick={report.close}>
            접수
          </Button>
        </Stack>
      </Modal>
      <Modal
        opened={closureOpened}
        onClose={() => {
          closure.close();
          setClosureState('idle');
        }}
        title="폐업 신고"
        centered
      >
        <Stack>
          <Text size="sm" c="dimmed">
            같은 브라우저의 중복 신고는 서버에서 자동 차단됩니다.
          </Text>
          <TextInput label="식당" value={selectedPlace?.name ?? ''} readOnly />
          <Button
            loading={closureState === 'submitting'}
            leftSection={<AlertTriangle size={16} />}
            onClick={() => void submitClosureReport()}
          >
            폐업 신고 접수
          </Button>
          {closureState === 'done' ? <Text size="sm">접수되었습니다.</Text> : null}
          {closureState === 'error' ? <Text size="sm" c="red">접수에 실패했습니다.</Text> : null}
        </Stack>
      </Modal>
    </AppShell>
  );

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
          note: 'web-ui-report',
        }),
      });
      if (!response.ok) throw new Error(`closure ${response.status}`);
      setClosureState('done');
      await loadPlaces();
    } catch {
      setClosureState('error');
    }
  }
}

function PlaceList({
  places,
  selectedId,
  onSelect,
}: {
  places: Place[];
  selectedId?: string;
  onSelect: (place: Place) => void;
}) {
  return (
    <ScrollArea h="100%">
      <Stack gap="xs" p="md">
        {places.map((place) => (
          <button
            className="place-row"
            data-active={place.id === selectedId}
            key={place.id}
            onClick={() => onSelect(place)}
          >
            <span className={`grade-dot grade-${gradeClass(place.grade)}`}>{place.grade}</span>
            <span>
              <strong>{place.name}</strong>
              <small>{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</small>
            </span>
          </button>
        ))}
      </Stack>
    </ScrollArea>
  );
}

function PlaceDetails({
  place,
  visits,
  onReport,
  onClosureReport,
}: {
  place: Place | null;
  visits: Visit[];
  onReport: () => void;
  onClosureReport: () => void;
}) {
  if (!place) {
    return (
      <div className="empty-panel">
        <Building2 size={28} />
        <Text>표시할 식당이 없습니다.</Text>
      </div>
    );
  }

  return (
    <ScrollArea h="100%">
      <Stack gap="md" p="lg">
        <Group gap="xs">
          <Badge className={`grade-badge grade-${gradeClass(place.grade)}`}>{gradeLabel(place.grade)}</Badge>
          {place.is_closed ? <Badge color="gray">폐업 제보</Badge> : null}
        </Group>
        <div>
          <Title order={2}>{place.name}</Title>
          <Text c="dimmed">{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</Text>
        </div>
        <div className="stat-grid">
          <Metric label="방문" value={`${place.visit_count_12m ?? 0}회`} />
          <Metric label="부서" value={`${place.unique_department_count_12m ?? 0}개`} />
          <Metric label="점수" value={Number(place.score ?? 0).toFixed(2)} />
        </div>
        <Stack gap="xs">
          <Text fw={700}>방문 기록</Text>
          {visits.slice(0, 10).map((visit) => (
            <a className="visit-row" href={visit.source_url ?? '#'} target="_blank" rel="noreferrer" key={visit.id}>
              <span>{visit.visit_date}</span>
              <strong>{visit.amount.toLocaleString('ko-KR')}원</strong>
              <small>{[visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ')}</small>
            </a>
          ))}
        </Stack>
        <Group grow>
          <Button variant="light" onClick={onReport}>
            정보 수정·삭제
          </Button>
          <Button variant="outline" color="gray" onClick={onClosureReport}>
            폐업 신고
          </Button>
        </Group>
      </Stack>
    </ScrollArea>
  );
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
}: {
  places: Place[];
  selectedPlace: Place | null;
  onSelect: (place: Place) => void;
}) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const [kakaoReady, setKakaoReady] = useState(false);

  useEffect(() => {
    if (!KAKAO_JS_KEY) return;
    let cancelled = false;
    loadKakao(KAKAO_JS_KEY)
      .then(() => {
        if (!cancelled) setKakaoReady(true);
      })
      .catch(() => {
        if (!cancelled) setKakaoReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!kakaoReady || !mapRef.current) return;
    const kakao = window.kakao;
    const center = new kakao.maps.LatLng(selectedPlace?.latitude ?? 37.5665, selectedPlace?.longitude ?? 126.978);
    const map = new kakao.maps.Map(mapRef.current, { center, level: 7 });
    const bounds = new kakao.maps.LatLngBounds();

    places
      .filter((place) => place.latitude && place.longitude)
      .forEach((place) => {
        const position = new kakao.maps.LatLng(place.latitude, place.longitude);
        bounds.extend(position);
        const marker = new kakao.maps.CustomOverlay({
          position,
          yAnchor: 1,
          content: `<button class="map-marker grade-${gradeClass(place.grade)}" data-place-id="${place.id}" aria-label="${place.name}">${place.grade}</button>`,
        });
        marker.setMap(map);
      });

    if (places.length > 1) {
      map.setBounds(bounds);
    }

    const listener = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const id = target.closest<HTMLButtonElement>('[data-place-id]')?.dataset.placeId;
      const place = places.find((item) => item.id === id);
      if (place) onSelect(place);
    };
    mapRef.current.addEventListener('click', listener);
    return () => mapRef.current?.removeEventListener('click', listener);
  }, [kakaoReady, onSelect, places, selectedPlace]);

  if (KAKAO_JS_KEY && kakaoReady) {
    return <div className="kakao-map" ref={mapRef} />;
  }

  return <FallbackMap places={places} selectedId={selectedPlace?.id} onSelect={onSelect} />;
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
  const located = places.filter((place) => place.latitude && place.longitude);
  return (
    <div className="fallback-map">
      {located.map((place) => {
        const left = (((place.longitude ?? 126.978) - 126.734) / (127.269 - 126.734)) * 100;
        const top = (1 - ((place.latitude ?? 37.5665) - 37.413) / (37.715 - 37.413)) * 100;
        return (
          <button
            className={`map-marker grade-${gradeClass(place.grade)}`}
            data-active={place.id === selectedId}
            key={place.id}
            style={{ left: `${left}%`, top: `${top}%` }}
            onClick={() => onSelect(place)}
            aria-label={place.name}
          >
            {place.grade}
          </button>
        );
      })}
    </div>
  );
}

function gradeLabel(grade: string) {
  if (grade === '★★★') return '강추';
  if (grade === '★★') return '추천';
  if (grade === '★') return '중립';
  return '신규';
}

function gradeClass(grade: string) {
  if (grade === '★★★') return 'top';
  if (grade === '★★') return 'good';
  if (grade === '★') return 'neutral';
  return 'new';
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
  if (window.kakao?.maps) {
    return Promise.resolve();
  }
  return new Promise<void>((resolve, reject) => {
    let settled = false;
    const timeout = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(new Error('kakao map timeout'));
    }, 2500);
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
