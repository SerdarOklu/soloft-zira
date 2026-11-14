# Frontend

Next.js App Router application built on `@soloft/uds`, the Soloft design system. Phase 1
provides the sign-in screen, the six-menu shell with role-based navigation, Turkish and
English, light and dark mode, and the system pages. The screens themselves are
placeholders until their phases (`../docs/phases.md`).

```bash
npm ci
npm run dev          # http://localhost:3000, needs the backend on http://localhost:8000
npm test
npm run build
npm run typecheck
```

## Access to the design system

`@soloft/uds` is installed from the private repository `SerdarOklu/soloft-uds`, pinned to
the tag `v0.2.0`. `npm ci` therefore needs GitHub access to that repository.

- **Developer machine:** an SSH key registered with a GitHub account that can read the
  repository is enough. The lock file records the dependency as `git+ssh`.
- **Without an SSH key:** tell git to use HTTPS, which then uses your normal GitHub
  credentials:

  ```bash
  git config --global url."https://github.com/".insteadOf "ssh://git@github.com/"
  git config --global --add url."https://github.com/".insteadOf "git@github.com:"
  ```

- **CI:** create a fine-grained personal access token with read-only **Contents** access
  to `SerdarOklu/soloft-uds` only, and save it in this repository as the Actions secret
  `UDS_READ_TOKEN` (Settings, Secrets and variables, Actions). Until the secret exists the
  frontend job fails at its first step and says why.

## Rules that come from the design system

These are recorded in `../docs/decisions/0002-frontend-nextjs-and-uds.md`:

- UDS is never modified from this repository. A gap is solved here and reported as a
  proposed addition to UDS.
- No colour literals. The one exception is `app/theme.css`, which sets the product accent.
- Every screen works in light and dark mode, on desktop and at 390 px.
- All copy comes from `messages/tr.json` and `messages/en.json`; both files must have the
  same keys, which `npm test` checks.

## How it fits together

| Path | Role |
| --- | --- |
| `proxy.ts` | Adds the locale prefix (`/tr`, `/en`) and negotiates the language |
| `i18n/` | Locales and locale-aware navigation |
| `messages/` | Interface texts |
| `app/[locale]/layout.tsx` | Root layout: theme, mode from the cookie, providers |
| `app/[locale]/login/` | Sign-in screen |
| `app/[locale]/(console)/` | The signed-in area; its layout redirects to sign-in without a session |
| `app/api/session/route.ts` | Sign in and sign out; keeps the access token in an httpOnly cookie |
| `lib/nav.ts` | The screens and which role sees each (PDT section 10.3) |
| `lib/session.ts` | Reads the signed-in user from the backend on every request |
| `components/` | Shell, sign-in, placeholder and system screens, all composed from UDS |

The browser never talks to the backend directly and never sees the access token. Set
`BACKEND_URL` if the backend is not on `http://localhost:8000`.

## Known gaps

- **No logo.** `components/brand.tsx` renders a text wordmark in the brand slots until
  Zira has logo artwork.
- **Fonts load from Google Fonts** through `@soloft/uds/fonts.css`. Self-host them before
  production (Phase 2).
- **The not-found page renders in the browser, not on the server.** The address returns
  status 404 and the localized page appears once the page script runs.

`AGENTS.md` in this folder is written by `next dev` itself for AI coding tools; it is
committed so the working tree stays clean.
