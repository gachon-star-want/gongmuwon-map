# Cloudflare Pages PR Preview Check

This project keeps production hosting on Vercel, but uses Cloudflare Pages as a free PR preview/check surface for the static Vite frontend.

## Cloudflare Pages Settings

Create a Pages project with Git integration:

- Project name: `gongmuwon-map-preview`
- Repository: `gachon-star-want/gongmuwon-map`
- Production branch: `main`
- Build command: `npm run build`
- Build output directory: `apps/web/dist`
- Preview deployments: enabled for all non-production branches
- PR comments: enabled

The repository includes `wrangler.jsonc` with `pages_build_output_dir` so the output directory stays source-controlled.

The repository also includes `apps/web/public/_headers`, which Vite copies to the Pages output root. It sets `X-Robots-Tag: noindex` for every Cloudflare Pages response. This is intentional: Cloudflare Pages is only a preview/check surface for this project, while canonical production remains on Vercel.

## Current Connection Status

Checked on 2026-05-31 with `wrangler whoami` and `wrangler pages project list --json`: the Cloudflare account is authenticated, but the Pages project list is empty (`[]`). The repository-side files are ready, but the Cloudflare dashboard still needs a Git-integrated Pages project connected to `gachon-star-want/gongmuwon-map`.

## Environment Variables

Set these for both Preview and Production in the Cloudflare Pages project:

- `VITE_API_BASE=https://xn--ob0bo0wl1ax52a.com`
- `VITE_KAKAO_JS_KEY=<restricted browser key>`
- `VITE_TURNSTILE_SITE_KEY=<Cloudflare Turnstile site key>`

Optional:

- `VITE_AD_SLOT_TEXT`
- `VITE_AD_SLOT_URL`

Do not add server-only secrets to Cloudflare Pages. The Pages project is only for frontend preview checks; Vercel remains the production API host. In particular, `TURNSTILE_SECRET_KEY` belongs only in Vercel API environment variables.

The Turnstile widget must allow the production hostname and Cloudflare Pages preview hostnames used by this project. If Cloudflare Pages uses `*.pages.dev` previews, include that Pages hostname pattern in the Turnstile widget domain allowlist.

## Expected PR Behavior

When a pull request originates from this repository, Cloudflare Pages creates a unique preview URL and updates the PR with deployment status. The preview URL should load the static app and call the production API through `VITE_API_BASE`.

After setup, verify on a test PR:

1. Cloudflare Pages check appears on the PR.
2. The preview URL opens successfully.
3. The response includes `X-Robots-Tag: noindex` for Cloudflare Pages responses.
4. Production deploy remains owned by Vercel after merge.
