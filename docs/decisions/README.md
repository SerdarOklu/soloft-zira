# Decisions

One short file per decision: what was decided, why, and what it rules out.
A decision marked **Open** is waiting for an answer and blocks the phase it names.

| No. | Decision | Status |
| --- | --- | --- |
| [0001](0001-monorepo-and-stack.md) | One repository; FastAPI, PostgreSQL with PostGIS, Redis with Celery, Docker Compose | Accepted |
| [0002](0002-frontend-nextjs-and-uds.md) | Frontend is Next.js App Router on the Soloft UDS design system | Accepted |
| [0003](0003-phase-order.md) | Eight phases in product order, one pull request each, Water Vault before Field Memory | Accepted |
| [0004](0004-accent-colour.md) | Product accent is khaki green, `#5E6B3B` | Accepted |
| [0005](0005-repository-visibility-and-uds.md) | Repository stays private for now; UDS is a private git dependency | Decided for now |
| [0006](0006-vps-resource-budget.md) | Memory budget on the KVM 2 VPS | Proposed (confirmed in Phase 2) |
| [0007](0007-precipitation-source.md) | NASA POWER is the primary precipitation source until Earth Engine works | Accepted |
| [0008](0008-sign-in-and-sessions.md) | Sign-in: backend access tokens, kept by the frontend in an httpOnly cookie | Accepted |
| [0009](0009-self-hosted-fonts.md) | Serve fonts from our own origin, not Google Fonts | Open (needs UDS access) |

Decisions about the model itself (fallow handling, starting storage, strategy rules,
uncertainty) are in PDT sections 7 and 15.
