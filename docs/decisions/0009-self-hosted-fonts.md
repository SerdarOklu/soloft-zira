# 0009: Self-hosted fonts

**Status:** Open, 14 November 2026. Blocked on read access to the private design system;
the mechanism below is agreed, the implementation and its check wait for the token.

## Decision

The production site serves its fonts from its own origin, not from Google Fonts. No page
makes a request to `fonts.googleapis.com` or `fonts.gstatic.com` at runtime.

## Why

Today the fonts load from Google Fonts through `@soloft/uds/fonts.css`
(`frontend/README.md`, "Known gaps"). In production that means:

- every visitor's browser calls a third party before the first paint, which is a privacy
  leak and a dependency on Google's availability;
- a request outside Türkiye to Google's CDN can be slow or blocked.

Self-hosting removes the third-party request and keeps the fonts under our control, on the
same HTTPS origin as the rest of the app.

## Why it is not done yet

The actual `@font-face` rules — the family name, the weights, the styles and the file
URLs — live inside `@soloft/uds/fonts.css`, which ships in the private `@soloft/uds`
package. We cannot read that file (and so cannot know which font and weights to host)
without read access to `SerdarOklu/soloft-uds` (the `UDS_READ_TOKEN`, see
[0005](0005-repository-visibility-and-uds.md)). We do not guess the family, and we do not
modify UDS ([0002](0002-frontend-nextjs-and-uds.md)). The same token blocks the frontend
image build, so both are unblocked together.

## How, once the token is available

Solve it inside Zira, without touching UDS:

1. During the frontend image build (which has the token and `@soloft/uds` installed), read
   `node_modules/@soloft/uds/fonts.css`, download the font files it references into
   `frontend/public/fonts/uds/`, and write a Zira stylesheet with the same `@font-face`
   rules pointing at those local files.
2. Import that local stylesheet from `app/globals.css` in place of
   `@import '@soloft/uds/fonts.css'`, so the UDS package is still the source of truth for
   which font is used, but the bytes come from our origin.
3. Verify: load the site and confirm the network panel shows no request to
   `fonts.googleapis.com` or `fonts.gstatic.com`, and the type renders unchanged in light
   and dark mode.

Report any gap found in UDS itself as a proposed addition to UDS, not a change here.

## Consequences

- Until this is done, a production deployment still fetches fonts from Google. The
  deployment is otherwise complete; this is the one Phase 2 item waiting on UDS access.
- `frontend/public/fonts/` exists for the hosted files.
