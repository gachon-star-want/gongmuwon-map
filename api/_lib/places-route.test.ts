import { beforeEach, describe, expect, it, vi } from 'vitest';
import handler from '../v1/places';
import placeByIdHandler from '../v1/places/[id]';
import searchHandler from '../v1/places/search';
import { readQuery } from './db';

vi.mock('./db', () => ({
  readQuery: vi.fn(),
}));

type MockResponse = {
  statusCode?: number;
  body?: unknown;
  headers: Map<string, unknown>;
  setHeader: (name: string, value: string) => void;
  status: (code: number) => MockResponse;
  json: (body: unknown) => MockResponse;
  end: () => void;
};

function mockResponse(): MockResponse {
  const headers = new Map<string, unknown>();
  return {
    headers,
    setHeader(name, value) {
      headers.set(name.toLowerCase(), value);
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(body) {
      this.body = body;
      return this;
    },
    end() {
      return undefined;
    },
  };
}

describe('/api/v1/places', () => {
  beforeEach(() => {
    vi.mocked(readQuery).mockReset();
    vi.mocked(readQuery).mockResolvedValue({ rows: [] } as never);
  });

  it('does not inject a Seoul bbox when bbox is omitted', async () => {
    const res = mockResponse();
    await handler({ method: 'GET', query: { limit: '25' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(200);
    expect(readQuery).toHaveBeenCalledTimes(1);
    const [sql, values] = vi.mocked(readQuery).mock.calls[0];
    expect(sql).toContain('latitude IS NOT NULL');
    expect(sql).toContain('longitude IS NOT NULL');
    expect(sql).not.toContain('latitude BETWEEN $1 AND $3');
    expect(values).toEqual([25]);
  });

  it('applies bbox and grade filters only when requested', async () => {
    const res = mockResponse();
    await handler(
      {
        method: 'GET',
        query: { bbox: '1,2,3,4', grade: '★★★,★', limit: '10' },
        headers: {},
      } as never,
      res as never,
    );

    expect(res.statusCode).toBe(200);
    const [sql, values] = vi.mocked(readQuery).mock.calls[0];
    expect(sql).toContain('latitude BETWEEN $1 AND $3');
    expect(sql).toContain('longitude BETWEEN $2 AND $4');
    expect(sql).toContain('grade = ANY($5::text[])');
    expect(sql).toContain('LIMIT $6');
    expect(values).toEqual([1, 2, 3, 4, ['★★★', '★'], 10]);
  });

  it('rejects malformed bbox instead of silently falling back to Seoul', async () => {
    const res = mockResponse();
    await handler({ method: 'GET', query: { bbox: 'bad' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'invalid_bbox' });
    expect(readQuery).not.toHaveBeenCalled();
  });
});

describe('/api/v1/places/[id]', () => {
  beforeEach(() => {
    vi.mocked(readQuery).mockReset();
    vi.mocked(readQuery).mockResolvedValue({ rows: [] } as never);
  });

  it('rejects malformed UUID ids before querying the database', async () => {
    const res = mockResponse();
    await placeByIdHandler({ method: 'GET', query: { id: 'not-a-uuid' }, headers: {} } as never, res as never);

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'invalid_place_id' });
    expect(readQuery).not.toHaveBeenCalled();
  });

  it('selects an explicit public detail column list', async () => {
    const res = mockResponse();
    await placeByIdHandler(
      { method: 'GET', query: { id: '11111111-1111-1111-1111-111111111111' }, headers: {} } as never,
      res as never,
    );

    const [sql] = vi.mocked(readQuery).mock.calls[0];
    expect(sql).not.toContain('SELECT *');
    expect(sql).toContain('id, name, road_address');
    expect(sql).not.toContain('valid_place');
    expect(sql).not.toContain('chain_brand');
  });
});

describe('/api/v1/places/search', () => {
  beforeEach(() => {
    vi.mocked(readQuery).mockReset();
    vi.mocked(readQuery).mockResolvedValue({ rows: [] } as never);
  });

  it('rejects queries shorter than 2 characters before querying the database', async () => {
    const res = mockResponse();
    await searchHandler(
      { method: 'GET', query: { q: '가', grade: '★★★' }, headers: {} } as never,
      res as never,
    );

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({ error: 'query_too_short' });
    expect(readQuery).not.toHaveBeenCalled();
  });

  it('accepts queries of 2 or more characters', async () => {
    const res = mockResponse();
    await searchHandler(
      { method: 'GET', query: { q: '카페', grade: '★★★' }, headers: {} } as never,
      res as never,
    );

    expect(res.statusCode).toBe(200);
    expect(readQuery).toHaveBeenCalledTimes(1);
  });
});
