export type CurrentUser = {
  id: string;
  handle: string;
  role: string;
  created_at: string;
};

type AuthResponse = {
  user: CurrentUser | null;
  error?: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function authFetch(path: string, body?: unknown) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = (await response.json()) as AuthResponse;
  if (!response.ok) {
    throw new Error(data.error || `auth_${response.status}`);
  }
  return data;
}

export async function getCurrentUser() {
  return (await authFetch('/api/auth/me')).user;
}

export async function login(handle: string, password: string) {
  return (await authFetch('/api/auth/login', { handle, password })).user;
}

export async function register(handle: string, password: string) {
  return (await authFetch('/api/auth/register', { handle, password })).user;
}

export async function logout() {
  await authFetch('/api/auth/logout', {});
}
