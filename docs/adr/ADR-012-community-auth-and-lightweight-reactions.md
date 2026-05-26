# ADR-012: Community, Login, and Lightweight Place Reactions

- **Status**: Accepted
- **Date**: 2026-05-26
- **Supersedes / narrows**: The blanket v1 ban on user participation in `LEGAL_PRIVACY.md` and `RISK_MITIGATION.md` is narrowed as described below. Free-form user comments/reviews remain banned on restaurant/place pages.

## Context

The service needs a lightweight community surface and basic login so users can talk to each other without attaching subjective reviews to official public-spending records.

The existing legal safety line banned user comments, ratings, and reviews because placing subjective text directly on a restaurant detail page can create defamation and business-interference risk.

## Decision

1. Add login-backed community features.
   - Public read is allowed.
   - Creating posts and comments requires login.
   - Community posts are not attached to `places.id`, coordinates, visit records, agencies, or source rows.
   - Community content is a separate board under `/community`.

2. Add place-level binary reactions only.
   - A place may receive only `like` or `dislike` from a logged-in user.
   - No free text, star score, review title, image upload, taste claim, or public voter list is attached to a place.
   - One user has at most one active reaction per place.

3. Keep restaurant/place pages free of user comments and reviews.
   - Place detail remains based on official public data plus binary reaction counts.
   - Free-form discussion belongs only in the separate community board.

4. Moderate by deletion/hide fields rather than hard delete.
   - Community rows support `hidden_at` / `deleted_at`.
   - Operator review can hide problematic content without mutating public data tables.

## Consequences

- Auth and community tables are app-owned tables, separate from public-spending data tables.
- Existing public API semantics remain unchanged for official data.
- New reaction counts must not be used as the official grade formula.
- Future expansion to restaurant-attached comments, star ratings, or reviews requires another ADR.

