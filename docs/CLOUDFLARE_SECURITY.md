# Cloudflare Security Setup

This project uses Vercel for production hosting/API routes and Cloudflare for low-cost security controls around preview checks, bot resistance, and edge filtering.

Official docs checked on 2026-05-31:

- Cloudflare Pages preview deployments: https://developers.cloudflare.com/pages/configuration/preview-deployments/
- Cloudflare Pages `_headers`: https://developers.cloudflare.com/pages/configuration/headers/
- Cloudflare Turnstile: https://developers.cloudflare.com/turnstile/
- Cloudflare Turnstile plans: https://developers.cloudflare.com/turnstile/plans/
- Cloudflare WAF custom rules: https://developers.cloudflare.com/waf/custom-rules/
- Cloudflare WAF rate limiting rules: https://developers.cloudflare.com/waf/rate-limiting-rules/

## Current Repository Controls

- Cloudflare Pages preview build output: `apps/web/dist` via `wrangler.jsonc`.
- Cloudflare Pages preview noindex: `apps/web/public/_headers` sets `X-Robots-Tag: noindex`.
- Turnstile frontend widget: enabled when `VITE_TURNSTILE_SITE_KEY` is present.
- Turnstile server verification: API routes call Cloudflare Siteverify through `TURNSTILE_SECRET_KEY` and fail closed when the secret, token, or verification is missing.
- Vercel CSP allows `https://challenges.cloudflare.com` for Turnstile script, iframe, and verification-related browser traffic.

## Current Production Edge Status

Checked on 2026-05-31:

- `dig +short xn--ob0bo0wl1ax52a.com NS` returns Vercel DNS (`ns1.vercel-dns.com`, `ns2.vercel-dns.com`).
- `curl -I https://xn--ob0bo0wl1ax52a.com/` returns `server: Vercel`.

That means Cloudflare WAF Custom Rules and Cloudflare Rate Limiting Rules are not currently in the production request path. They can only protect production after the domain is onboarded to Cloudflare DNS/proxy, or after another Cloudflare edge product is placed in front of Vercel. Until then, the app-side API guards and Vercel deployment settings remain the active production controls.

## Turnstile

Create one Managed widget in Cloudflare Turnstile.

Checked on 2026-05-31: Wrangler OAuth is authenticated, but the token does not have Turnstile widget API permissions (`GET /accounts/{account_id}/challenges/widgets` returns 403). Create the widget in the Cloudflare dashboard or with a separate API token that has Turnstile widget write access.

Allowed hostnames:

- `xn--ob0bo0wl1ax52a.com`
- the Vercel production host, if different
- Cloudflare Pages preview hostnames for `gongmuwon-map-preview`
- local development hostnames only if needed for manual testing

Environment variables:

| Target | Variable | Secret? | Notes |
|---|---|---:|---|
| Vercel Production/Preview API | `TURNSTILE_SECRET_KEY` | yes | Server-only Siteverify secret. |
| Vercel frontend build | `VITE_TURNSTILE_SITE_KEY` | no | Browser site key. |
| Cloudflare Pages preview | `VITE_TURNSTILE_SITE_KEY` | no | Needed because Pages previews render the static app. |

Protected write routes:

- `POST /api/takedown-request`
- `POST /api/closure-report`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/community/posts`
- `POST /api/community/posts/{id}/comments`

Do not add `TURNSTILE_SECRET_KEY` to Cloudflare Pages. Pages is static preview only and should never receive server secrets.

## WAF Custom Rules

Prerequisite: production traffic must pass through Cloudflare. This is not true while the primary domain uses Vercel DNS directly.

Free plan rule budget is limited, so keep rules coarse and high-value.

Recommended rules:

1. Block direct public access to `/api/cron/*` unless the request is from Vercel Cron or carries the expected authorization path. The app already fail-closes on `CRON_SECRET`; the WAF rule reduces noise.
2. Managed Challenge high-risk bot traffic targeting `POST /api/auth/login`.
3. Managed Challenge high-risk bot traffic targeting `POST /api/takedown-request` and `POST /api/closure-report`.
4. Block nonstandard methods on `/api/*` except `GET`, `HEAD`, `POST`, and `OPTIONS`.
5. Block obvious path probes against `/wp-*`, `/.env`, `/phpmyadmin`, and similar non-app paths.

If the Cloudflare dashboard rule budget is exhausted, keep rule 1 and rule 2 first.

## Rate Limiting Rule

Prerequisite: production traffic must pass through Cloudflare. This is not true while the primary domain uses Vercel DNS directly.

Free plan rate limiting is coarse. Use the single rule as an edge backstop for write APIs, not as the primary correctness layer.

Recommended expression:

```text
(http.request.uri.path eq "/api/auth/login"
 or http.request.uri.path eq "/api/auth/register"
 or http.request.uri.path eq "/api/takedown-request"
 or http.request.uri.path eq "/api/closure-report"
 or http.request.uri.path eq "/api/community/posts"
 or starts_with(http.request.uri.path, "/api/community/posts/"))
and http.request.method eq "POST"
```

Recommended action:

- Mitigation: Managed Challenge or Block, depending on false-positive tolerance.
- Characteristics: IP.
- Period: the smallest Free-plan-supported window.
- Threshold: start conservatively, then tighten after reviewing Cloudflare analytics.

The app-side Vercel in-memory limiter remains in place. Cloudflare rate limiting is a cross-instance backstop.
