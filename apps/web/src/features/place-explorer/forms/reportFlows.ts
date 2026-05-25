import { API_BASE } from '../publicData';

export async function submitClosureReport(input: { placeId: string; note: string | null }) {
  const response = await fetch(`${API_BASE}/api/closure-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      place_id: input.placeId,
      reporter_fp: browserFingerprint(),
      note: input.note ?? 'web-ui-report',
    }),
  });

  if (!response.ok) throw new Error(`closure ${response.status}`);
  return response;
}

export async function submitTakedownRequest(input: {
  placeId: string;
  reason: string;
  email: string | null;
}) {
  const response = await fetch(`${API_BASE}/api/takedown-request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      place_id: input.placeId,
      reason: input.reason,
      email: input.email,
    }),
  });

  if (!response.ok) throw new Error(`takedown ${response.status}`);
  return response;
}

export function browserFingerprint(): string {
  const key = 'public-officer-map-fp';
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const next = crypto.randomUUID();
  window.localStorage.setItem(key, next);
  return next;
}
