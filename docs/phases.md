# Development phases

Each phase is one branch and one pull request. Work stops at the end of a phase; the next
one starts only after the pull request is approved and merged.

| Phase | Branch | Scope | Approval criterion | Status |
| --- | --- | --- | --- | --- |
| 0. Repository skeleton | `faz-0/repo-iskeleti` | Monorepo layout, README, PDT copy, configuration files from the parameter sheet, `.env.example`, development Compose, CI | Database and Redis start with one command; CI is green; no business logic | In review (PR #1) |
| 1. Base infrastructure | `faz-1/temel-altyapi` | FastAPI app structure, first migration for the 16 tables, login and three roles, Celery; Next.js with Soloft UDS: six-menu shell, login screen, system pages, Turkish and English, light and dark | A user signs in and sees the empty menus; migrations run | In review |
| 2. First deployment to the VPS | `faz-2/vps-dagitim` | Production Compose, Nginx with HTTPS, memory limits, images built in GitHub Actions, backup script, runbook | The skeleton is reachable over HTTPS on the domain | In review (PR #3); live at `https://zira.soloftindustries.com` |
| 3. Fields, NASA POWER, Data Center | `faz-3/tarlalar-power` | Field records with polygons, POWER client and cache, fetch jobs, Data Center screens | A field is added, 25 years of data is fetched and displayed | In review (PR #4); live at `https://zira.soloftindustries.com` |
| 4. Water Vault | `faz-4/su-kasasi` | ET0, Kc curve, daily water balance, uncertainty; tests against FAO-56 worked examples; screens | Usable water on the decision day is shown in mm | Decision-day water built and checked; the crop season waits for the stage lengths ([0011](decisions/0011-water-vault-version-1.md)) |
| 5. Field Memory | `faz-5/tarla-hafizasi` | Earth Engine: Landsat and MODIS, NDVI, cropped or fallow classification, confirmation screen | The 10-year history is shown and confirmed by the user | Built on MODIS NDVI read from the public Planetary Computer catalogue, not Earth Engine ([0013](decisions/0013-field-memory-from-modis.md)); Landsat not connected |
| 6. Rotation and Zira Card | `faz-6/rotasyon-kart` | Strategies A, B and C, the six metrics, card and export | Three rotations are compared on one card | Built with provisional season values and a user-supplied rotation ([0012](decisions/0012-rotation-demo-and-whatsapp.md)); WhatsApp drafts with agronomist approval added |
| 7. Sensors and cooperative | `faz-7/sensor-kooperatif` | Sensor ingest, simulator, cooperative panel, farmer view | Simulator data corrects the Water Vault | Not started |

## Differences from the PDT

- **Water Vault before Field Memory.** PDT section 13.2 builds Field Memory first. Here the
  Water Vault comes first because it needs only NASA POWER, while Field Memory needs Earth
  Engine access that is not set up yet. The rotation engine can run on a hand-entered
  history marked as user-supplied until Field Memory exists.
- **Deployment is its own phase.** The PDT folds the VPS into its phase 0. Here it is
  phase 2, so the skeleton and base infrastructure are reviewed before anything is hosted.

## Order

Product order, 0 to 7. A faster order for the Space Apps submission (0, then 3, 4 and 6
without login or the VPS) was offered and not taken.

## Server

One Hostinger KVM 2 VPS dedicated to Zira: 2 vCPU (shared), 8 GB RAM, 100 GB NVMe.
The memory budget is in [decisions/0006-vps-resource-budget.md](decisions/0006-vps-resource-budget.md).
