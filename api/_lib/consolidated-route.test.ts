import { describe, expect, it } from 'vitest';
import { withId } from '../[...path]';

describe('consolidated API route helpers', () => {
  it('adds id without cloning away request fields', async () => {
    const req = {
      method: 'POST',
      query: { path: 'v1/places/place-1/reactions' },
      headers: { cookie: '' },
    };
    const res = {};

    await withId(
      async (nextReq) => {
        expect(nextReq).toBe(req);
        expect(nextReq.headers).toEqual({ cookie: '' });
        expect(nextReq.query).toEqual({ path: 'v1/places/place-1/reactions', id: 'place-1' });
      },
      req as never,
      res as never,
      'place-1',
    );

    expect(req.query).toEqual({ path: 'v1/places/place-1/reactions' });
  });
});
