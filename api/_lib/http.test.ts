import { describe, expect, it } from 'vitest';
import { reporterFingerprint } from './http';

function mockRequest(headers: Record<string, string>, remoteAddress = '10.0.0.1') {
  return {
    headers,
    socket: { remoteAddress },
  } as never;
}

describe('reporterFingerprint', () => {
  it('uses server-observed request data', () => {
    const first = reporterFingerprint(
      mockRequest({
        'x-forwarded-for': '203.0.113.10, 198.51.100.5',
        'user-agent': 'Browser A',
      }),
    );
    const second = reporterFingerprint(
      mockRequest({
        'x-forwarded-for': '203.0.113.10, 198.51.100.99',
        'user-agent': 'Browser A',
      }),
    );

    expect(first).toBe(second);
    expect(first).toHaveLength(64);
  });

  it('changes when the observed browser boundary changes', () => {
    const first = reporterFingerprint(mockRequest({ 'x-forwarded-for': '203.0.113.10', 'user-agent': 'Browser A' }));
    const second = reporterFingerprint(mockRequest({ 'x-forwarded-for': '203.0.113.10', 'user-agent': 'Browser B' }));

    expect(first).not.toBe(second);
  });
});
