# 0008: Sign-in and sessions

**Status:** Accepted, 14 November 2026

## Decision

- The backend owns accounts. `POST /api/v1/auth/login` checks the password (Argon2 hash)
  and returns a signed access token (JWT, HS256, 12 hours by default). Every other
  endpoint reads the token from the `Authorization: Bearer` header and loads the user
  from the database on each request, so a deactivated account loses access at once.
- The browser never sees the token. The Next.js route `/api/session` forwards the
  credentials to the backend and stores the token in an httpOnly, SameSite=Lax cookie
  (`zira_session`), sent over HTTPS only in production. Server components read the cookie
  and call the backend with it.
- Roles are `admin`, `agronomist` and `cooperative_user`; `farmer` is defined for phase 7.
  The API enforces roles (`require_roles`); the interface only hides what a role may not
  open (PDT section 10.3).
- Accounts are created by staff with `python -m app.cli create-user`. There is no
  self-registration and no password reset yet.

## Why

The soloft-uds design system leaves authentication to the product. Zira's backend is
FastAPI, not Next.js, so the session lives where the data is and the frontend stays a
thin, presentation-only layer. An httpOnly cookie keeps the token away from page scripts.

## Consequences

- Sign-in fails the same way for a wrong password and an unknown email, and takes the
  same time for both.
- The email is not validated as an address at sign-in: internal domains such as
  `name@cooperative.local` must work.
- Production refuses to start with the placeholder `SECRET_KEY` or one under 32 characters.
- Still to do in later phases: user management screens (phase 7), password reset, rate
  limiting of sign-in attempts (phase 2, at Nginx), token revocation on sign-out. Until
  then a signed-out token stays valid until it expires, although the browser no longer
  holds it.
