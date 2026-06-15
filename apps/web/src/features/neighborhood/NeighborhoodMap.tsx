import { useEffect, useMemo, useRef, useState } from 'react';
import { loadKakao } from '../place-explorer/map/kakaoLoader';
import type { BoundaryFeature } from './neighborhoodApi';

interface NeighborhoodMapProps {
  features: BoundaryFeature[];
  selected: string | null;
  onSelect: (admCd: string) => void;
}

const LENS_LABEL: Record<string, string> = {
  overall: '종합',
  convenience: '생활편의',
  education: '교육·보육',
  vitality: '인구·활력',
  welfare: '복지·문화',
  safety: '안전',
  housing: '주택',
  environment: '자연·환경',
};

// 렌즈별 값: 종합=거주 매칭 점수, 분야=시군구 내 분야 percentile (가구원수 독립)
function valueOf(f: BoundaryFeature, lens: string): number | null {
  if (lens === 'overall') return f.properties.score;
  const fields = f.properties.fields;
  return fields && fields[lens] != null ? fields[lens] : null;
}

// 시군구 내 상위일수록 진한 단색(teal). 결측은 회색. 빨강=나쁨 금지(ADR-015).
function lensColor(v: number | null): string {
  if (v === null || Number.isNaN(v)) return '#cbd5e1';
  const t = Math.max(0, Math.min(100, v)) / 100;
  return `hsl(173, 58%, ${86 - t * 50}%)`;
}

type PolyEntry = { admCd: string; feature: BoundaryFeature; polygons: any[] };

export function NeighborhoodMap({ features, selected, onSelect }: NeighborhoodMapProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const polysRef = useRef<PolyEntry[]>([]);
  const onSelectRef = useRef(onSelect);
  const [kakaoReady, setKakaoReady] = useState(false);
  const [lens, setLens] = useState('overall');
  const KAKAO_JS_KEY = import.meta.env.VITE_KAKAO_JS_KEY as string | undefined;

  const lenses = useMemo(() => {
    const cats = new Set<string>();
    for (const f of features) {
      if (f.properties.fields) for (const c of Object.keys(f.properties.fields)) cats.add(c);
    }
    const ordered = ['convenience', 'education', 'vitality', 'welfare', 'safety', 'housing', 'environment'].filter((c) => cats.has(c));
    return ['overall', ...ordered];
  }, [features]);

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

  // 폴리곤 생성(features 변경 시)
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
          const latlng = new kakao.maps.LatLng(pt[1], pt[0]);
          bounds.extend(latlng);
          hasCoords = true;
          return latlng;
        });
        const poly = new kakao.maps.Polygon({
          path,
          strokeWeight: 1,
          strokeColor: '#475569',
          strokeOpacity: 0.6,
          fillColor: lensColor(valueOf(feature, lens)),
          fillOpacity: 0.65,
        });
        poly.setMap(map);
        const admCd = feature.properties.adm_cd;
        kakao.maps.event.addListener(poly, 'click', () => onSelectRef.current(admCd));
        polygons.push(poly);
      }
      polysRef.current.push({ admCd: feature.properties.adm_cd, feature, polygons });
    }

    if (hasCoords) map.setBounds(bounds);
    // features가 바뀌면 lens 효과가 아래 useEffect로 색을 다시 입힌다
  }, [features, kakaoReady]); // eslint-disable-line react-hooks/exhaustive-deps

  // 렌즈/선택 변경 시 색·강조 갱신
  useEffect(() => {
    if (!kakaoReady) return;
    for (const entry of polysRef.current) {
      const on = entry.admCd === selected;
      const fill = lensColor(valueOf(entry.feature, lens));
      entry.polygons.forEach((p) =>
        p.setOptions({
          fillColor: fill,
          strokeWeight: on ? 3 : 1,
          strokeColor: on ? '#1d4ed8' : '#475569',
          fillOpacity: on ? 0.82 : 0.65,
        }),
      );
    }
  }, [lens, selected, features, kakaoReady]);

  if (!KAKAO_JS_KEY) return null;

  return (
    <div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
        {lenses.map((l) => (
          <button
            key={l}
            type="button"
            onClick={() => setLens(l)}
            style={{
              padding: '4px 12px',
              borderRadius: 16,
              border: '1px solid #cbd5e1',
              background: lens === l ? '#0f766e' : '#fff',
              color: lens === l ? '#fff' : '#334155',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {LENS_LABEL[l] ?? l}
          </button>
        ))}
      </div>

      <div ref={mapRef} style={{ width: '100%', height: 360, borderRadius: 12, overflow: 'hidden' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, fontSize: 11, color: '#64748b', flexWrap: 'wrap' }}>
        <span>옅음</span>
        <span style={{ display: 'inline-block', width: 80, height: 8, borderRadius: 4, background: 'linear-gradient(90deg, hsl(173,58%,86%), hsl(173,58%,36%))' }} />
        <span>진함(상위)</span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginLeft: 8 }}>
          <span style={{ width: 10, height: 10, background: '#cbd5e1', borderRadius: 2, display: 'inline-block' }} />
          자료 없음
        </span>
        <span style={{ marginLeft: 'auto' }}>같은 시군구 내 비교 · {LENS_LABEL[lens] ?? lens}</span>
      </div>
    </div>
  );
}
