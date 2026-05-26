import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Group, Loader, Select, Stack, Text, Textarea, TextInput, Title } from '@mantine/core';
import { LogIn, MapPin, MessageCircle, Plus, Send, UserRound } from 'lucide-react';
import mascotLogo from '../../assets/officer-mascot-logo.png';
import { SponsorAd } from '../ads/SponsorAd';
import { AuthModal } from '../auth/AuthModal';
import type { CurrentUser } from '../auth/authApi';
import { getCurrentUser, logout } from '../auth/authApi';
import {
  createComment,
  createPost,
  loadComments,
  loadPosts,
  type CommunityCategory,
  type CommunityComment,
  type CommunityPost,
} from './communityApi';
import './styles.css';

const categories: { value: CommunityCategory | 'all'; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'free', label: '자유' },
  { value: 'question', label: '질문' },
  { value: 'meetup', label: '번개' },
  { value: 'tip', label: '팁' },
  { value: 'notice', label: '공지' },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(
    new Date(value),
  );
}

export function CommunityPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [category, setCategory] = useState<CommunityCategory | 'all'>('all');
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [comments, setComments] = useState<CommunityComment[]>([]);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [commentBody, setCommentBody] = useState('');
  const [postCategory, setPostCategory] = useState<CommunityCategory>('free');
  const selectedPost = useMemo(() => posts.find((post) => post.id === selectedPostId) ?? posts[0] ?? null, [posts, selectedPostId]);

  useEffect(() => {
    void getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    void refreshPosts();
  }, [category]);

  useEffect(() => {
    if (!selectedPost) {
      setComments([]);
      return;
    }
    setSelectedPostId(selectedPost.id);
    void loadComments(selectedPost.id).then(setComments).catch(() => setComments([]));
  }, [selectedPost?.id]);

  async function refreshPosts() {
    setLoading(true);
    try {
      const next = await loadPosts(category);
      setPosts(next);
      if (next.length && !next.some((post) => post.id === selectedPostId)) {
        setSelectedPostId(next[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  async function submitPost() {
    if (!user) {
      setAuthOpen(true);
      return;
    }
    const created = await createPost({ category: postCategory, title: title.trim(), body: body.trim() });
    setTitle('');
    setBody('');
    await refreshPosts();
    setSelectedPostId(created.id);
  }

  async function submitComment() {
    if (!selectedPost) return;
    if (!user) {
      setAuthOpen(true);
      return;
    }
    await createComment(selectedPost.id, commentBody.trim());
    setCommentBody('');
    setComments(await loadComments(selectedPost.id));
    await refreshPosts();
  }

  return (
    <main className="community-shell">
      <header className="community-topbar">
        <a className="community-brand" href="/">
          <img src={mascotLogo} alt="" aria-hidden />
          <span>공무원맵</span>
        </a>
        <nav>
          <a href="/">
            <MapPin size={16} aria-hidden />
            지도
          </a>
          <a href="/community" data-active="true">
            <MessageCircle size={16} aria-hidden />
            커뮤니티
          </a>
        </nav>
        {user ? (
          <Button variant="light" leftSection={<UserRound size={16} />} onClick={() => void logout().then(() => setUser(null))}>
            {user.handle}
          </Button>
        ) : (
          <Button leftSection={<LogIn size={16} />} onClick={() => setAuthOpen(true)}>
            로그인
          </Button>
        )}
      </header>

      <section className="community-layout">
        <aside className="community-rank">
          <Text fw={800}>소통방</Text>
          <SponsorAd variant="rail" />
        </aside>

        <section className="community-board" aria-label="커뮤니티 게시글">
          <Group justify="space-between" className="community-board-head">
            <div>
              <Title order={1}>커뮤니티</Title>
            </div>
            <Select
              w={130}
              value={category}
              onChange={(value) => setCategory((value as CommunityCategory | 'all') ?? 'all')}
              data={categories}
            />
          </Group>

          <section className="community-composer">
            <Group gap="xs">
              <Select
                w={110}
                value={postCategory}
                onChange={(value) => setPostCategory((value as CommunityCategory) ?? 'free')}
                data={categories.filter((item) => item.value !== 'all')}
              />
              <TextInput
                className="community-title-input"
                placeholder={user ? '제목' : '로그인 후 글을 쓸 수 있습니다'}
                value={title}
                onChange={(event) => setTitle(event.currentTarget.value)}
              />
            </Group>
            <Textarea
              minRows={3}
              placeholder="내용"
              value={body}
              onChange={(event) => setBody(event.currentTarget.value)}
            />
            <Button
              leftSection={<Plus size={16} />}
              disabled={title.trim().length < 2 || !body.trim()}
              onClick={() => void submitPost()}
            >
              글 올리기
            </Button>
          </section>

          {loading ? (
            <div className="community-loading">
              <Loader size="sm" />
            </div>
          ) : (
            <div className="community-post-list">
              {posts.map((post) => (
                <button
                  type="button"
                  className="community-post-row"
                  data-active={post.id === selectedPost?.id}
                  key={post.id}
                  onClick={() => setSelectedPostId(post.id)}
                >
                  <Badge variant="light">{categories.find((item) => item.value === post.category)?.label ?? post.category}</Badge>
                  <strong>{post.title}</strong>
                  <span>{post.author_handle} · 댓글 {post.comment_count} · {formatDate(post.created_at)}</span>
                </button>
              ))}
              {!posts.length ? <Text c="dimmed">아직 게시글이 없습니다.</Text> : null}
            </div>
          )}
        </section>

        <aside className="community-detail" aria-label="게시글 상세">
          {selectedPost ? (
            <>
              <div className="community-detail-head">
                <Badge variant="light">{categories.find((item) => item.value === selectedPost.category)?.label}</Badge>
                <Title order={2}>{selectedPost.title}</Title>
                <Text size="sm" c="dimmed">
                  {selectedPost.author_handle} · {formatDate(selectedPost.created_at)}
                </Text>
              </div>
              <Text className="community-post-body">{selectedPost.body}</Text>
              <Stack gap="xs" className="community-comments">
                <Text fw={800}>댓글 {comments.length.toLocaleString('ko-KR')}</Text>
                {comments.map((comment) => (
                  <div className="community-comment" key={comment.id}>
                    <strong>{comment.author_handle}</strong>
                    <span>{formatDate(comment.created_at)}</span>
                    <p>{comment.body}</p>
                  </div>
                ))}
              </Stack>
              <div className="community-comment-form">
                <Textarea
                  minRows={2}
                  placeholder={user ? '댓글을 입력하세요' : '로그인 후 댓글을 쓸 수 있습니다'}
                  value={commentBody}
                  onChange={(event) => setCommentBody(event.currentTarget.value)}
                />
                <Button leftSection={<Send size={16} />} disabled={!commentBody.trim()} onClick={() => void submitComment()}>
                  등록
                </Button>
              </div>
            </>
          ) : (
            <Text c="dimmed">게시글을 선택하세요.</Text>
          )}
        </aside>
      </section>
      <AuthModal opened={authOpen} onClose={() => setAuthOpen(false)} onAuthenticated={setUser} />
    </main>
  );
}
