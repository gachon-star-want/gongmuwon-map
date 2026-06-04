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
  onBoundsChange?: (bbox: [number, number, number, number], level: number) => void;
  desktopListOpen?: boolean;
};

type MarkerEntry = {
  marker: any;
  place: Place;
  listener: () => void;
};

type Coordinates = {
  latitude: number;
  longitude: number;
};

const DEFAULT_MAP_LEVEL = 5;
const USER_LOCATION_LEVEL = 4;

export function MapCanvas({ places, selectedPlace, onSelect, onBlankClick, onBoundsChange, desktopListOpen = true }: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const clustererRef = useRef<any>(null);
  const markersRef = useRef<MarkerEntry[]>([]);
  const userMarkerRef = useRef<any>(null);
  const onSelectRef = useRef(onSelect);
  const onBlankClickRef = useRef(onBlankClick);
  const onBoundsChangeRef = useRef(onBoundsChange);
  const hasRequestedLocationRef = useRef(false);
  const [kakaoReady, setKakaoReady] = useState(false);
  const [kakaoFailed, setKakaoFailed] = useState(false);
  const [userLocation, setUserLocation] = useState<Coordinates | null>(null);
  const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;

  useEffect(() => {
    onSelectRef.current = onSelect;
    onBlankClickRef.current = onBlankClick;
    onBoundsChangeRef.current = onBoundsChange;
  }, [onBlankClick, onBoundsChange, onSelect]);

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
    const map = new kakao.maps.Map(mapRef.current, { center, level: DEFAULT_MAP_LEVEL });
    const clusterer = new kakao.maps.MarkerClusterer({
      map,
      averageCenter: true,
      minLevel: 7,
      disableClickZoom: true,
      styles: [
        {
          width: '40px',
          height: '40px',
          background: '#dc2626',
          color: '#fff',
          border: '2.5px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 4px 14px rgba(220,38,38,0.45)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '37px',
          fontSize: '13px',
        },
        {
          width: '50px',
          height: '50px',
          background: '#ea580c',
          color: '#fff',
          border: '2.5px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 4px 14px rgba(234,88,12,0.45)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '47px',
          fontSize: '14px',
        },
        {
          width: '60px',
          height: '60px',
          background: '#4f46e5',
          color: '#fff',
          border: '2.5px solid #fff',
          borderRadius: '999px',
          boxShadow: '0 4px 14px rgba(79,70,229,0.45)',
          textAlign: 'center',
          fontWeight: '800',
          lineHeight: '57px',
          fontSize: '15px',
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
    // Fire bounds on every idle (pan/zoom end)
    const fireBounds = () => {
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      const level = map.getLevel();
      const bbox: [number, number, number, number] = [sw.getLat(), sw.getLng(), ne.getLat(), ne.getLng()];
      onBoundsChangeRef.current?.(bbox, level);
    };
    kakao.maps.event.addListener(map, 'idle', fireBounds);
    fireBounds();
  }, [kakaoReady]);

  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current || hasRequestedLocationRef.current) return;
    hasRequestedLocationRef.current = true;
    if (!navigator.geolocation) return;

    const kakao = window.kakao;
    const map = mapInstanceRef.current;
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const location = { latitude: coords.latitude, longitude: coords.longitude };
        setUserLocation(location);
        map.setLevel(USER_LOCATION_LEVEL);
        map.setCenter(new kakao.maps.LatLng(location.latitude, location.longitude));
        const bounds = map.getBounds();
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const bbox: [number, number, number, number] = [sw.getLat(), sw.getLng(), ne.getLat(), ne.getLng()];
        onBoundsChangeRef.current?.(bbox, USER_LOCATION_LEVEL);
      },
      () => {
        map.setLevel(DEFAULT_MAP_LEVEL);
        map.setCenter(new kakao.maps.LatLng(SEOUL_CENTER.latitude, SEOUL_CENTER.longitude));
        const bounds = map.getBounds();
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const bbox: [number, number, number, number] = [sw.getLat(), sw.getLng(), ne.getLat(), ne.getLng()];
        onBoundsChangeRef.current?.(bbox, DEFAULT_MAP_LEVEL);
      },
      { enableHighAccuracy: true, maximumAge: 300000, timeout: 5000 },
    );
  }, [kakaoReady]);

  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current || !clustererRef.current) return;
    const kakao = window.kakao;
    const clusterer = clustererRef.current;

    clusterer.clear();
    markersRef.current.forEach(({ marker, listener }) => {
      kakao.maps.event.removeListener(marker, 'click', listener);
      marker.setMap(null);
    });
    markersRef.current = [];

    const entries = places
      .filter((place) => place.latitude && place.longitude)
      .map((place) => {
        const position = new kakao.maps.LatLng(place.latitude, place.longitude);
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
  }, [kakaoReady, places, selectedPlace?.id]);

  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current || !userLocation) return;
    const kakao = window.kakao;
    const position = new kakao.maps.LatLng(userLocation.latitude, userLocation.longitude);
    if (userMarkerRef.current) {
      userMarkerRef.current.setPosition(position);
      return;
    }
    userMarkerRef.current = new kakao.maps.Marker({
      map: mapInstanceRef.current,
      position,
      title: '현재 위치',
      image: createCurrentLocationImage(kakao),
      zIndex: 50,
    });
  }, [kakaoReady, userLocation]);

  useEffect(() => {
    if (!kakaoReady) return;
    const kakao = window.kakao;
    markersRef.current.forEach(({ marker, place }) => {
      const selected = selectedPlace?.id === place.id;
      marker.setImage(createMarkerImage(kakao, place, selected));
      marker.setZIndex(selected ? 30 : 10);
    });
  }, [kakaoReady, selectedPlace?.id, places]);

  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current || !selectedPlace || !selectedPlace.latitude || !selectedPlace.longitude) return;
    const kakao = window.kakao;
    const position = new kakao.maps.LatLng(selectedPlace.latitude, selectedPlace.longitude);
    mapInstanceRef.current.panTo(position);
    
    if (window.innerWidth > 767) {
      setTimeout(() => {
        if (!mapInstanceRef.current) return;
        let offset = 0;
        if (desktopListOpen) {
          offset = 380;
        } else {
          offset = 200;
        }
        if (offset > 0) {
          mapInstanceRef.current.panBy(offset, 0);
        }
      }, 50);
    }
  }, [kakaoReady, selectedPlace?.id, desktopListOpen]);

  if (!KAKAO_JS_KEY || kakaoFailed) {
    return <FallbackMap places={places} selectedId={selectedPlace?.id} onSelect={onSelect} />;
  }

  return <div className="kakao-map" ref={mapRef} aria-label="카카오 지도" />;
}

function markerAccessibleName(place: Place) {
  return `${gradeLabel(place.grade)} 등급, ${place.name}, ${shortRegionLabel(place.road_address_part ?? '지역 미상')}`;
}

function createCurrentLocationImage(kakao: any) {
  const size = 26;
  const svg = encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <circle cx="${size / 2}" cy="${size / 2}" r="10" fill="#2563eb" fill-opacity="0.18"/>
      <circle cx="${size / 2}" cy="${size / 2}" r="6" fill="#2563eb" stroke="#fff" stroke-width="3"/>
    </svg>
  `);
  return new kakao.maps.MarkerImage(`data:image/svg+xml;charset=utf-8,${svg}`, new kakao.maps.Size(size, size), {
    offset: new kakao.maps.Point(size / 2, size / 2),
  });
}
