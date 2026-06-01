export type MapBounds = {
  minLatitude: number;
  minLongitude: number;
  maxLatitude: number;
  maxLongitude: number;
};

export const SEOUL_CENTER = { latitude: 37.5665, longitude: 126.978 };
export const KOREA_BOUNDS: MapBounds = {
  minLatitude: 33,
  minLongitude: 124,
  maxLatitude: 39,
  maxLongitude: 132,
};

export function positionStyle(latitude: number, longitude: number, bounds: MapBounds = KOREA_BOUNDS) {
  const longitudeSpan = Math.max(0.001, bounds.maxLongitude - bounds.minLongitude);
  const latitudeSpan = Math.max(0.001, bounds.maxLatitude - bounds.minLatitude);
  const left = ((longitude - bounds.minLongitude) / longitudeSpan) * 100;
  const top = (1 - (latitude - bounds.minLatitude) / latitudeSpan) * 100;
  return {
    left: `${Math.min(96, Math.max(4, left))}%`,
    top: `${Math.min(92, Math.max(8, top))}%`,
  };
}

export function average(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

export function boundsForCoordinates(points: { latitude: number; longitude: number }[]): MapBounds {
  if (!points.length) return KOREA_BOUNDS;
  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const latitudePadding = Math.max(0.05, (maxLatitude - minLatitude) * 0.12);
  const longitudePadding = Math.max(0.05, (maxLongitude - minLongitude) * 0.12);
  return {
    minLatitude: minLatitude - latitudePadding,
    minLongitude: minLongitude - longitudePadding,
    maxLatitude: maxLatitude + latitudePadding,
    maxLongitude: maxLongitude + longitudePadding,
  };
}
