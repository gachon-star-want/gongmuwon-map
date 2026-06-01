import { describe, expect, it } from 'vitest';
import { average, boundsForCoordinates, KOREA_BOUNDS, positionStyle } from './geo';

describe('geo helpers', () => {
  it('average computes mean', () => {
    expect(average([1, 2, 3])).toBe(2);
  });

  it('positionStyle clamps to expected bounds', () => {
    const style = positionStyle(37.5665, 126.978);
    expect(parseFloat(style.left)).toBeCloseTo(37.225);
    expect(parseFloat(style.top)).toBeCloseTo(23.8917);
  });

  it('positionStyle accepts dynamic nationwide bounds', () => {
    const bounds = boundsForCoordinates([
      { latitude: 35.17, longitude: 129.07 },
      { latitude: 37.57, longitude: 126.98 },
    ]);
    const busan = positionStyle(35.17, 129.07, bounds);
    const seoul = positionStyle(37.57, 126.98, bounds);

    expect(parseFloat(busan.left)).toBeCloseTo(90.3226);
    expect(parseFloat(busan.top)).toBeCloseTo(90.3226);
    expect(parseFloat(seoul.left)).toBeCloseTo(9.6774);
    expect(parseFloat(seoul.top)).toBeCloseTo(9.6774);
  });

  it('boundsForCoordinates falls back to Korea bounds for empty input', () => {
    expect(boundsForCoordinates([])).toEqual(KOREA_BOUNDS);
  });
});
