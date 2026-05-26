CREATE TABLE IF NOT EXISTS public.app_users (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  handle text NOT NULL,
  handle_normalized text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  password_salt text NOT NULL,
  role text NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'moderator', 'admin')),
  created_at timestamptz NOT NULL DEFAULT now(),
  last_login_at timestamptz,
  deleted_at timestamptz,
  CHECK (char_length(handle) BETWEEN 2 AND 24)
);

CREATE TABLE IF NOT EXISTS public.app_sessions (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
  token_hash text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS app_sessions_user_expires ON public.app_sessions (user_id, expires_at DESC);

CREATE TABLE IF NOT EXISTS public.community_posts (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  author_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE RESTRICT,
  category text NOT NULL DEFAULT 'free' CHECK (category IN ('free', 'question', 'meetup', 'tip', 'notice')),
  title text NOT NULL CHECK (char_length(title) BETWEEN 2 AND 80),
  body text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 4000),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  hidden_at timestamptz,
  deleted_at timestamptz
);

CREATE INDEX IF NOT EXISTS community_posts_visible_created ON public.community_posts (created_at DESC)
  WHERE hidden_at IS NULL AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS public.community_comments (
  id uuid PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
  post_id uuid NOT NULL REFERENCES public.community_posts(id) ON DELETE CASCADE,
  author_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE RESTRICT,
  body text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 1000),
  created_at timestamptz NOT NULL DEFAULT now(),
  hidden_at timestamptz,
  deleted_at timestamptz
);

CREATE INDEX IF NOT EXISTS community_comments_post_created ON public.community_comments (post_id, created_at)
  WHERE hidden_at IS NULL AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS public.place_reactions (
  place_id uuid NOT NULL REFERENCES public.places(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
  reaction text NOT NULL CHECK (reaction IN ('like', 'dislike')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (place_id, user_id)
);

CREATE INDEX IF NOT EXISTS place_reactions_place ON public.place_reactions (place_id);

CREATE OR REPLACE VIEW public.community_posts_public WITH (security_barrier = true) AS
SELECT
  p.id,
  p.category,
  p.title,
  p.body,
  p.created_at,
  p.updated_at,
  u.handle AS author_handle,
  COUNT(c.id)::integer AS comment_count,
  MAX(c.created_at) AS last_comment_at
FROM public.community_posts p
JOIN public.app_users u ON u.id = p.author_id
LEFT JOIN public.community_comments c
  ON c.post_id = p.id
  AND c.hidden_at IS NULL
  AND c.deleted_at IS NULL
WHERE p.hidden_at IS NULL
  AND p.deleted_at IS NULL
  AND u.deleted_at IS NULL
GROUP BY p.id, u.handle;

CREATE OR REPLACE VIEW public.community_comments_public WITH (security_barrier = true) AS
SELECT
  c.id,
  c.post_id,
  c.body,
  c.created_at,
  u.handle AS author_handle
FROM public.community_comments c
JOIN public.community_posts p ON p.id = c.post_id
JOIN public.app_users u ON u.id = c.author_id
WHERE c.hidden_at IS NULL
  AND c.deleted_at IS NULL
  AND p.hidden_at IS NULL
  AND p.deleted_at IS NULL
  AND u.deleted_at IS NULL;

CREATE OR REPLACE VIEW public.place_reaction_counts WITH (security_barrier = true) AS
SELECT
  place_id,
  COUNT(*) FILTER (WHERE reaction = 'like')::integer AS like_count,
  COUNT(*) FILTER (WHERE reaction = 'dislike')::integer AS dislike_count
FROM public.place_reactions
GROUP BY place_id;

ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.place_reactions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.app_users, public.app_sessions, public.community_posts,
  public.community_comments, public.place_reactions FROM anon, authenticated;

GRANT SELECT ON public.community_posts_public TO anon, authenticated;
GRANT SELECT ON public.community_comments_public TO anon, authenticated;
GRANT SELECT ON public.place_reaction_counts TO anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
    GRANT SELECT ON public.community_posts_public TO app_readonly;
    GRANT SELECT ON public.community_comments_public TO app_readonly;
    GRANT SELECT ON public.place_reaction_counts TO app_readonly;
  END IF;
END;
$$;
