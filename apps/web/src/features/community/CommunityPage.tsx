import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Group, Loader, Select, Stack, Text, Textarea, TextInput, Title } from '@mantine/core';
import { LogIn, MapPin, MessageCircle, Plus, Send, UserRound } from 'lucide-react';
import mascotLogo from '../../assets/officer-mascot-logo.png';
import { SponsorAd } from '../ads/SponsorAd';
import { AuthModal } from '../auth/AuthModal';
import type { CurrentUser } from '../auth/authApi';
import { getCurrentUser, logout } from '../auth/authApi';
import { TurnstileWidget } from '../../shared/TurnstileWidget';
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

function formatApiError(error: unknown) {
  const code = error instanceof Error ? error.message : '';
  if (code === 'login_required') return '로그인이 필요합니다.';
  if (code === 'invalid_post') return '제목은 2~80자, 내용은 1~4000자여야 합니다.';
  if (code === 'invalid_comment') return '댓글은 1~1000자여야 합니다.';
  if (code === 'not_found') return '해당 게시글을 찾을 수 없습니다.';
  if (code.startsWith('turnstile_')) return '보안 확인을 다시 시도해주세요.';
  return '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.';
}

function isAuthRequiredError(error: unknown) {
  return error instanceof Error && error.message === 'login_required';
}

export function CommunityPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [category, setCategory] = useState<CommunityCategory | 'all'>('all');
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [comments, setComments] = useState<CommunityComment[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);
  const [commentsError, setCommentsError] = useState<string | null>(null);
  const [postSubmitError, setPostSubmitError] = useState<string | null>(null);
  const [commentSubmitError, setCommentSubmitError] = useState<string | null>(null);
  const [postSubmitting, setPostSubmitting] = useState(false);
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [commentBody, setCommentBody] = useState('');
  const [postCategory, setPostCategory] = useState<CommunityCategory>('free');
  const [postTurnstileToken, setPostTurnstileToken] = useState<string | null>(null);
  const [commentTurnstileToken, setCommentTurnstileToken] = useState<string | null>(null);
  const [postTurnstileReset, setPostTurnstileReset] = useState(0);
  const [commentTurnstileReset, setCommentTurnstileReset] = useState(0);
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
      setCommentsError(null);
      setCommentTurnstileToken(null);
      setCommentTurnstileReset((value) => value + 1);
      return;
    }
    setCommentTurnstileToken(null);
    setCommentTurnstileReset((value) => value + 1);
    void loadSelectedPostComments();
  }, [selectedPost?.id]);

  async function loadSelectedPostComments() {
    if (!selectedPost) return;
    setLoadingComments(true);
    setCommentsError(null);
    try {
      setComments(await loadComments(selectedPost.id));
    } catch (error) {
      setComments([]);
      setCommentsError(formatApiError(error));
    } finally {
      setLoadingComments(false);
    }
  }

  async function refreshPosts() {
    setLoadingPosts(true);
    setPostsError(null);
    try {
      const next = await loadPosts(category);
      setPosts(next);
      if (next.length && !next.some((post) => post.id === selectedPostId)) {
        setSelectedPostId(next[0].id);
      }
      if (!next.length) {
        setSelectedPostId(null);
      }
    } catch (error) {
      setPosts([]);
      setSelectedPostId(null);
      setPostsError(formatApiError(error));
    } finally {
      setLoadingPosts(false);
    }
  }

  async function submitPost() {
    if (!user) {
      setAuthOpen(true);
      return;
    }
    if (title.trim().length < 2 || !body.trim()) return;
    if (!postTurnstileToken) {
      setPostSubmitError('보안 확인을 완료해주세요.');
      return;
    }
    setPostSubmitting(true);
    setPostSubmitError(null);
    setPostsError(null);
    try {
      const created = await createPost({
        category: postCategory,
        title: title.trim(),
        body: body.trim(),
        turnstileToken: postTurnstileToken,
      });
      setTitle('');
      setBody('');
      setPostTurnstileToken(null);
      setPostTurnstileReset((value) => value + 1);
      setSelectedPostId(created.id);
      await refreshPosts();
    } catch (error) {
      setPostSubmitError(formatApiError(error));
      setPostTurnstileToken(null);
      setPostTurnstileReset((value) => value + 1);
      if (isAuthRequiredError(error)) {
        setAuthOpen(true);
        setUser(null);
      }
    } finally {
      setPostSubmitting(false);
    }
  }

  async function submitComment() {
    if (!selectedPost) return;
    if (!user) {
      setAuthOpen(true);
      return;
    }
    if (!commentBody.trim()) return;
    if (!commentTurnstileToken) {
      setCommentSubmitError('보안 확인을 완료해주세요.');
      return;
    }
    setCommentSubmitting(true);
    setCommentSubmitError(null);
    try {
      await createComment(selectedPost.id, commentBody.trim(), commentTurnstileToken);
      setCommentBody('');
      setCommentTurnstileToken(null);
      setCommentTurnstileReset((value) => value + 1);
      setComments(await loadComments(selectedPost.id));
      await refreshPosts();
    } catch (error) {
      setCommentSubmitError(formatApiError(error));
      setCommentTurnstileToken(null);
      setCommentTurnstileReset((value) => value + 1);
      if (isAuthRequiredError(error)) {
        setAuthOpen(true);
        setUser(null);
      }
    } finally {
      setCommentSubmitting(false);
    }
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
            {!user ? (
              <div className="community-auth-inline" role="note">
                <Text size="sm" c="dimmed">
                  글 작성은 로그인한 사용자만 가능합니다. 로그인은 닉네임·비밀번호 기반 인증만 사용합니다.
                </Text>
                <Button size="xs" variant="light" leftSection={<LogIn size={14} />} onClick={() => setAuthOpen(true)}>
                  로그인하고 글쓰기
                </Button>
              </div>
            ) : null}
            <Group gap="xs">
              <Select
                w={110}
                value={postCategory}
                onChange={(value) => setPostCategory((value as CommunityCategory) ?? 'free')}
                data={categories.filter((item) => item.value !== 'all')}
              />
              <TextInput
                className="community-title-input"
                placeholder={user ? '제목' : '로그인 후 작성 가능'}
                disabled={!user}
                value={title}
                onChange={(event) => {
                  setTitle(event.currentTarget.value);
                  if (postSubmitError) setPostSubmitError(null);
                }}
              />
            </Group>
            <Textarea
              minRows={3}
              placeholder="내용"
              disabled={!user}
              value={body}
              onChange={(event) => {
                setBody(event.currentTarget.value);
                if (postSubmitError) setPostSubmitError(null);
              }}
            />
            {user ? (
              <TurnstileWidget
                action="community_post"
                resetSignal={postTurnstileReset}
                onTokenChange={setPostTurnstileToken}
              />
            ) : null}
            {postSubmitError ? <Text size="sm" c="red">{postSubmitError}</Text> : null}
            <Button
              leftSection={<Plus size={16} />}
              loading={postSubmitting}
              disabled={!user || title.trim().length < 2 || !body.trim() || !postTurnstileToken}
              onClick={() => void submitPost()}
            >
              글 올리기
            </Button>
            {postSubmitError ? (
              <Button size="xs" variant="subtle" onClick={() => void submitPost()}>
                다시 시도
              </Button>
            ) : null}
          </section>

          {loadingPosts ? (
            <div className="community-state community-state-loading" role="status">
              <Loader size="sm" />
              <Text size="sm">게시글을 불러오는 중입니다.</Text>
            </div>
          ) : postsError ? (
            <div className="community-state community-state-error" role="alert">
              <Text size="sm">{postsError}</Text>
              <Button size="xs" variant="light" onClick={() => void refreshPosts()}>
                다시 시도
              </Button>
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
                {loadingComments ? (
                  <div className="community-state community-state-loading" role="status">
                    <Loader size="sm" />
                    <Text size="sm">댓글을 불러오는 중입니다.</Text>
                  </div>
                ) : commentsError ? (
                  <div className="community-state community-state-error" role="alert">
                    <Text size="sm">{commentsError}</Text>
                    <Button size="xs" variant="light" onClick={() => void loadSelectedPostComments()}>
                      다시 시도
                    </Button>
                  </div>
                ) : comments.length ? (
                  comments.map((comment) => (
                    <div className="community-comment" key={comment.id}>
                      <strong>{comment.author_handle}</strong>
                      <span>{formatDate(comment.created_at)}</span>
                      <p>{comment.body}</p>
                    </div>
                  ))
                ) : (
                  <Text c="dimmed">아직 댓글이 없습니다.</Text>
                )}
              </Stack>
              <div className="community-comment-form">
                {!user ? (
                  <div className="community-auth-inline" role="note">
                    <Text size="sm" c="dimmed">
                      댓글 작성은 로그인 후 가능합니다.
                    </Text>
                    <Button size="xs" variant="light" leftSection={<LogIn size={14} />} onClick={() => setAuthOpen(true)}>
                      로그인하고 댓글달기
                    </Button>
                  </div>
                ) : null}
                <Textarea
                  minRows={2}
                  placeholder={user ? '댓글을 입력하세요' : '로그인 후 댓글을 쓸 수 있습니다'}
                  disabled={!user}
                  value={commentBody}
                  onChange={(event) => {
                    setCommentBody(event.currentTarget.value);
                    if (commentSubmitError) setCommentSubmitError(null);
                  }}
                />
                {user ? (
                  <TurnstileWidget
                    action="community_comment"
                    resetSignal={`${selectedPost.id}-${commentTurnstileReset}`}
                    onTokenChange={setCommentTurnstileToken}
                  />
                ) : null}
                {commentSubmitError ? <Text size="sm" c="red">{commentSubmitError}</Text> : null}
                <Button
                  leftSection={<Send size={16} />}
                  loading={commentSubmitting}
                  disabled={!user || !commentBody.trim() || !commentTurnstileToken}
                  onClick={() => void submitComment()}
                >
                  등록
                </Button>
                {commentSubmitError ? (
                  <Button size="xs" variant="subtle" onClick={() => void submitComment()}>
                    다시 시도
                  </Button>
                ) : null}
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
