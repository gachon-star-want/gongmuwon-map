import { ActionIcon, Button, Loader, Group, ScrollArea, Stack, Text } from '@mantine/core';
import { RefreshCw, RotateCcw, X } from 'lucide-react';
import type { Place } from '../types';
import { formatDate, gradeClass, markerLabel } from '../format';

type PlaceListProps = {
  places: Place[];
  selectedId?: string;
  loading: boolean;
  error?: string | null;
  resultLabel?: string;
  hasActiveFilter?: boolean;
  onSelect: (place: Place) => void;
  onClose?: () => void;
  onReset: () => void;
  onRetry?: () => void;
};

export function PlaceList({
  places,
  selectedId,
  loading,
  error,
  resultLabel,
  hasActiveFilter,
  onSelect,
  onClose,
  onReset,
  onRetry,
}: PlaceListProps) {
  return (
    <div className="sheet-content">
      <Group justify="space-between" wrap="nowrap" className="sheet-header">
        <div>
          <Text fw={800}>식당 목록</Text>
          <Text size="xs" c="dimmed">
            {loading ? '검색 중' : (resultLabel ?? `${places.length.toLocaleString('ko-KR')}곳`)}
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
      ) : error ? (
        <div className="sheet-empty" role="alert">
          <Text fw={700}>목록을 불러오지 못했습니다.</Text>
          <Text size="sm" c="dimmed">
            네트워크 상태를 확인한 뒤 다시 시도해주세요.
          </Text>
          {onRetry ? (
            <Button size="xs" variant="light" leftSection={<RefreshCw size={14} />} onClick={onRetry}>
              다시 시도
            </Button>
          ) : null}
        </div>
      ) : places.length ? (
        <ScrollArea className="sheet-scroll">
          <div className="result-state-bar">
            <Text size="xs" c="dimmed">
              {hasActiveFilter ? '검색·필터 조건이 지도와 목록에 동일하게 적용됩니다.' : '최근 12개월 공식 공개자료 기준입니다.'}
            </Text>
            {hasActiveFilter ? (
              <Button size="compact-xs" variant="subtle" leftSection={<RotateCcw size={13} />} onClick={onReset}>
                초기화
              </Button>
            ) : null}
          </div>
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
          <Text size="sm" c="dimmed">
            검색어, 자치구, 등급, 폐업 포함 조건을 조정해보세요.
          </Text>
          <Button size="xs" variant="light" leftSection={<RotateCcw size={14} />} onClick={onReset}>
            필터 초기화
          </Button>
        </div>
      )}
    </div>
  );
}
