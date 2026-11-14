# 0002: Next.js App Router on Soloft UDS

**Status:** Accepted, 14 November 2026

## Decision

The frontend is a Next.js App Router application that takes its visual layer from
`@soloft/uds` (the Soloft Unified Design System), pinned to a release tag.

The PDT left "React or Next.js" open. UDS settles it: its integration guide targets the
Next.js App Router, and it supplies the shell, the console components, the login screens
and the system pages Zira needs.

| Zira screen | UDS pieces |
| --- | --- |
| Six-menu frame | `AppShell` |
| Dashboard | `PageHero`, `KpiGrid`, `KpiCard`, `Panel` |
| Fields list | `EntityCard`, `EntityRow`, `Toolbar`, `SearchField` |
| Data Center | `StatusBadge`, `ActivityList`, `Table` |
| Login and errors | `AuthLayout`, `LoginForm`, system pages |

## Rules taken from UDS

- UDS is not modified from this repository. A gap is solved inside Zira and reported as a
  proposed addition to UDS.
- No colour literals in component styles; every colour comes from a `--uds-*` token.
- Every screen works in light and dark mode.
- All copy comes from the translation files (Turkish and English); none is hard-coded.
- Routes, permissions, data and authentication stay in Zira; UDS is presentation only.

## Known gaps

UDS has no chart and no map component. Zira needs both: the NDVI series and water-balance
charts, and drawing a field boundary. Libraries are chosen in the phases that need them
(3 for the map, 4 for charts) and styled with UDS tokens.

## Consequences

- From Phase 1 on, installing the frontend needs read access to the private
  `SerdarOklu/soloft-uds` repository, on developer machines, in CI and on the build that
  produces the production image. See decision 0005.
- React 19 and Node 22.12 or newer, matching UDS.
- Phase 0 ships a plain placeholder page without UDS, so that CI is green before the
  access question is settled.
