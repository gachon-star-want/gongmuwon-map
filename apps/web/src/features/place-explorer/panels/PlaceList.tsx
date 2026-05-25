import { ActionIcon, Button, Loader, Group, ScrollArea, Stack, Text } from '@mantine/core';
import { RotateCcw, X } from 'lucide-react';
import type { Place } from '../types';
import { formatDate, gradeClass, markerLabel } from '../format';

type PlaceListProps = {
  places: Place[];
  selectedId?: string;
  loading: boolean;
  onSelect: (place: Place) => void;
  onClose?: () => void;
  onReset: () => void;
};

export function PlaceList({ places, selectedId, loading, onSelect, onClose, onReset }: PlaceListProps) {
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
