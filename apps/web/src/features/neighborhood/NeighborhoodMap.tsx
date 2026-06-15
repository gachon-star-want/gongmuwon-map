import { useEffect, useRef, useState } from 'react';
import { loadKakao } from '../place-explorer/map/kakaoLoader';
import type { BoundaryFeature } from './neighborhoodApi';

interface NeighborhoodMapProps {
  features: BoundaryFeature[];
  selected: string | null;
  onSelect: (admCd: string) => void;
}

// 시군구 내 점수(0~100) → teal 명도 그라데이션, 결측은 회색
function scoreColor(score: number | null): string {
  if (score === null || Number.isNaN(score)) return '#cbd5e1';
  const t = Math.max(0, Math.min(100, score)) / 100;
  const lightness = 86 - t * 50; // 낮은 점수=밝음, 높은 점수=진함
  return `hsl(173, 58%, ${lightness}%)`;
}

type PolyEntry = { admCd: string; polygons: any[] };

export function NeighborhoodMap({ features, selected, onSelect }: NeighborhoodMapProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const polysRef = useRef<PolyEntry[]>([]);
  const onSelectRef = useRef(onSelect);
  const [kakaoReady, setKakaoReady] = useState(false);
  const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!KAKAO_JS_KEY) return;
    let cancelled = false;
    loadKakao(KAKAO_JS_KEY)
      .then(() => {
        if (!cancelled) setKakaoReady(true);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [KAKAO_JS_KEY]);

  useEffect(() => {
    if (!kakaoReady || !mapRef.current || mapInstanceRef.current) return;
    const kakao = window.kakao;
    mapInstanceRef.current = new kakao.maps.Map(mapRef.current, {
      center: new kakao.maps.LatLng(36.5, 127.8),
      level: 9,
    });
  }, [kakaoReady]);

  // features 변경 시 폴리곤 재그리기
  useEffect(() => {
    if (!kakaoReady || !mapInstanceRef.current) return;
    const kakao = window.kakao;
    const map = mapInstanceRef.current;

    polysRef.current.forEach((entry) => entry.polygons.forEach((p) => p.setMap(null)));
    polysRef.current = [];

    const bounds = new kakao.maps.LatLngBounds();
    let hasCoords = false;

    for (const feature of features) {
      const geometry = feature.geometry as { type?: string; coordinates?: any };
      if (!geometry || !geometry.coordinates) continue;
      const rings = geometry.type === 'MultiPolygon' ? geometry.coordinates : [geometry.coordinates];
      const polygons: any[] = [];
      for (const polygon of rings) {
        const outer = polygon?.[0];
        if (!Array.isArray(outer)) continue;
        const path = outer.map((pt: number[]) => {
          const latlng = new kakao.maps.LatLng(pt[1], pt[0]); // GeoJSON [lng,lat] → LatLng(lat,lng)
          bounds.extend(latlng);
          hasCoords = true;
          return latlng;
        });
        const poly = new kakao.maps.Polygon({
          path,
          strokeWeight: 1,
          strokeColor: '#475569',
          strokeOpacity: 0.6,
          fillColor: scoreColor(feature.properties.score),
          fillOpacity: 0.65,
        });
        poly.setMap(map);
        const admCd = feature.properties.adm_cd;
        kakao.maps.event.addListener(poly, 'click', () => onSelectRef.current(admCd));
        polygons.push(poly);
      }
      polysRef.current.push({ admCd: feature.properties.adm_cd, polygons });
    }

    if (hasCoords) map.setBounds(bounds);
  }, [features, kakaoReady]);

  // 선택 읍면동 강조
  useEffect(() => {
    if (!kakaoReady) return;
    for (const entry of polysRef.current) {
      const on = entry.admCd === selected;
      entry.polygons.forEach((p) =>
        p.setOptions({
          strokeWeight: on ? 3 : 1,
          strokeColor: on ? '#1d4ed8' : '#475569',
          fillOpacity: on ? 0.82 : 0.65,
        }),
      );
    }
  }, [selected, features, kakaoReady]);

  if (!KAKAO_JS_KEY) return null;
  return <div ref={mapRef} style={{ width: '100%', height: 360, borderRadius: 12, overflow: 'hidden' }} />;
}
