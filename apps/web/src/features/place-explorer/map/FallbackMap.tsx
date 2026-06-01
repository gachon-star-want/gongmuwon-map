import { Button } from '@mantine/core';
import { Layers } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Place } from '../types';
import { gradeClass, markerLabel, shortRegionLabel } from '../format';
import { average, boundsForCoordinates, positionStyle } from './geo';
import { SEOUL_CENTER } from './geo';

type FallbackMapProps = {
  places: Place[];
  selectedId?: string;
  onSelect: (place: Place) => void;
};

export function FallbackMap({ places, selectedId, onSelect }: FallbackMapProps) {
  const located = places.filter((place) => place.latitude && place.longitude);
  const bounds = useMemo(
    () => boundsForCoordinates(located.map((place) => ({ latitude: place.latitude!, longitude: place.longitude! }))),
    [located],
  );
  const clusters = useClusters(located);
  const [expandedRegion, setExpandedRegion] = useState<string | null>(null);
  const markerPlaces = expandedRegion
    ? located.filter((place) => (place.road_address_part ?? '지역 미상') === expandedRegion)
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
              style={positionStyle(cluster.latitude, cluster.longitude, bounds)}
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
          style={positionStyle(place.latitude ?? SEOUL_CENTER.latitude, place.longitude ?? SEOUL_CENTER.longitude, bounds)}
          onClick={() => onSelect(place)}
          aria-label={`${place.name} ${place.road_address_part ?? ''}`}
        >
          {markerLabel(place.grade)}
        </button>
      ))}
    </div>
  );
}

function useClusters(places: Place[]) {
  return useMemo(() => {
    const grouped = new Map<string, Place[]>();
    places.forEach((place) => {
      const region = place.road_address_part ?? '지역 미상';
      grouped.set(region, [...(grouped.get(region) ?? []), place]);
    });
    return Array.from(grouped.entries()).map(([region, items]) => ({
      region,
      items,
      latitude: average(items.map((item) => item.latitude ?? SEOUL_CENTER.latitude)),
      longitude: average(items.map((item) => item.longitude ?? SEOUL_CENTER.longitude)),
    }));
  }, [places]);
}
