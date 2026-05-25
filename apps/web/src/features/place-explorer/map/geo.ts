export const SEOUL_CENTER = { latitude: 37.5665, longitude: 126.978 };

export function positionStyle(latitude: number, longitude: number) {
  const left = ((longitude - 126.734) / (127.269 - 126.734)) * 100;
  const top = (1 - (latitude - 37.413) / (37.715 - 37.413)) * 100;
  return {
    left: `${Math.min(96, Math.max(4, left))}%`,
    top: `${Math.min(92, Math.max(8, top))}%`,
  };
}

export function average(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}
