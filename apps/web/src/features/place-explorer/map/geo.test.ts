import { describe, expect, it } from 'vitest';
import { average, positionStyle } from './geo';

describe('geo helpers', () => {
  it('average computes mean', () => {
    expect(average([1, 2, 3])).toBe(2);
  });

  it('positionStyle clamps to expected bounds', () => {
    const style = positionStyle(37.5665, 126.978);
    expect(style.left).toBe('45.60747663551305%');
    expect(style.top).toBe('49.172185430464346%');
  });
});
