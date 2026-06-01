import { useEffect, useRef, useState } from 'react';
import { loadKakao } from './kakaoLoader';
import { createMarkerImage } from './markerImage';
import { FallbackMap } from './FallbackMap';
import { SEOUL_CENTER } from './geo';
import type { Place } from '../types';
import { gradeLabel, shortRegionLabel } from '../format';

type MapCanvasProps = {
  places: Place[];
  selectedPlace: Place | null;
  onSelect: (place: Place) => void;
  onBlankClick: () => void;
};

type MarkerEntry = {
  marker: any;
  place: Place;
  listener: () => void;
};

export function MapCanvas({ places, selectedPlace, onSelect, onBlankClick }: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const clustererRef = useRef<any>(null);
  const markersRef = useRef<MarkerEntry[]>([]);
  const onSelectRef = useRef(onSelect);
  const onBlankClickRef = useRef(onBlankClick);
  const hasFitBoundsRef = useRef(false);
  const [kakaoReady, setKakaoReady] = useState(false);
  const [kakaoFailed, setKakaoFailed] = useState(false);
  const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;

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
  }, [KAKAO_JS_KEY]);

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
          boxShadow: '0 10px 24px rgba(15, 23, 42, 0.24)',
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
          boxShadow: '0 10px 24px rgba(15, 23, 42, 0.24)',
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
          boxShadow: '0 10px 24px rgba(15, 23, 42, 0.24)',
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
    } else if (entries.length === 1 && !hasFitBoundsRef.current) {
      map.setCenter(entries[0].marker.getPosition());
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

  return <div className="kakao-map" ref={mapRef} aria-label="카카오 지도" />;
}

function markerAccessibleName(place: Place) {
  return `${gradeLabel(place.grade)} 등급, ${place.name}, ${shortRegionLabel(place.road_address_part ?? '지역 미상')}`;
}
