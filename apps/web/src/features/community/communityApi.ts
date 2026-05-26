export type CommunityCategory = 'free' | 'question' | 'meetup' | 'tip' | 'notice';

export type CommunityPost = {
  id: string;
  category: CommunityCategory;
  title: string;
  body: string;
  author_handle: string;
  comment_count: number;
  created_at: string;
  updated_at: string;
  last_comment_at: string | null;
};

export type CommunityComment = {
  id: string;
  post_id: string;
  body: string;
  author_handle: string;
  created_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function jsonFetch<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    credentials: 'include',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = (await response.json()) as T & { error?: string };
  if (!response.ok) throw new Error(data.error || `community_${response.status}`);
  return data;
}

export async function loadPosts(category?: CommunityCategory | 'all') {
  const params = new URLSearchParams({ limit: '50' });
  if (category && category !== 'all') params.set('category', category);
  return (await jsonFetch<{ items: CommunityPost[] }>(`/api/community/posts?${params}`)).items;
}

export async function createPost(input: { category: CommunityCategory; title: string; body: string }) {
  return jsonFetch<{ id: string }>('/api/community/posts', input);
}

export async function loadComments(postId: string) {
  return (await jsonFetch<{ items: CommunityComment[] }>(`/api/community/posts/${postId}/comments`)).items;
}

export async function createComment(postId: string, body: string) {
  return jsonFetch<{ id: string }>(`/api/community/posts/${postId}/comments`, { body });
}
