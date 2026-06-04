import type { Grade, Place } from '../types';
import { gradeColor, markerLabel } from '../format';

export function createMarkerImage(kakao: any, place: Place, selected: boolean) {
  const base = markerSize(place.grade);
  const size = base + (selected ? 4 : 0);
  const w = size + 12; // pill width
  const h = size;
  const color = gradeColor(place.grade);
  const opacity = place.is_closed ? 0.38 : 1;
  const label = markerLabel(place.grade);
  const rx = h / 2; // fully rounded pill
  const fontSize = 10;

  // Drop shadow filter for depth
  const shadow = selected
    ? `<filter id="s"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="${color}" flood-opacity="0.55"/></filter>`
    : `<filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="rgba(0,0,0,0.35)" flood-opacity="1"/></filter>`;

  // Selection ring
  const ring = selected
    ? `<rect x="1" y="1" width="${w - 2}" height="${h - 2}" rx="${rx - 1}" fill="none" stroke="#fff" stroke-width="2.5" opacity="${opacity}"/>`
    : '';

  const svg = encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <defs>${shadow}</defs>
  <rect x="0" y="0" width="${w}" height="${h}" rx="${rx}" fill="${color}" fill-opacity="${opacity}" filter="url(#s)"/>
  ${ring}
  <text x="${w / 2}" y="${h / 2 + fontSize * 0.36}" text-anchor="middle" font-family="'Apple SD Gothic Neo','Noto Sans KR',sans-serif" font-weight="800" font-size="${fontSize}" fill="#fff" letter-spacing="0">${label}</text>
</svg>`);

  return new kakao.maps.MarkerImage(
    `data:image/svg+xml;charset=utf-8,${svg}`,
    new kakao.maps.Size(w, h),
    { offset: new kakao.maps.Point(w / 2, h / 2) },
  );
}

function markerSize(grade: Grade) {
  if (grade === '★★★') return 26;
  if (grade === '★★') return 24;
  return 22;
}
