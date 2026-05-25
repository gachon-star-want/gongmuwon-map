import type { Grade, Place } from '../types';
import { markerLabel } from '../format';

export function createMarkerImage(kakao: any, place: Place, selected: boolean) {
  const size = markerSize(place.grade) + (selected ? 4 : 0);
  const color = gradeColor(place.grade);
  const opacity = place.is_closed ? 0.35 : 1;
  const label = markerLabel(place.grade);
  const svg = encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size + 6}" viewBox="0 0 ${size} ${size + 6}">
      <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 2}" fill="${color}" fill-opacity="${opacity}" stroke="#fff" stroke-width="2"/>
      ${selected ? `<circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 1}" fill="none" stroke="#172033" stroke-width="3"/>` : ''}
      <text x="50%" y="${size / 2 + 4}" text-anchor="middle" font-family="Arial, sans-serif" font-weight="800" font-size="${label === 'NEW' ? 9 : 10}" fill="#fff">${label}</text>
    </svg>
  `);
  return new kakao.maps.MarkerImage(`data:image/svg+xml;charset=utf-8,${svg}`, new kakao.maps.Size(size, size + 6), {
    offset: new kakao.maps.Point(size / 2, size + 2),
  });
}

function markerSize(grade: Grade) {
  if (grade === '★★★') return 34;
  if (grade === '★★') return 30;
  return 26;
}

function gradeColor(grade: Grade) {
  if (grade === '★★★') return '#ef4444';
  if (grade === '★★') return '#f59e0b';
  if (grade === '★') return '#6b7280';
  return '#3b82f6';
}
