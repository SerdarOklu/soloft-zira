# 0005: Repository visibility and the private UDS dependency

**Status:** Decided for now, 14 November 2026: the repository stays private and will be
opened later. The choice among the options below is made when it is opened.

## The conflict

- The Space Apps submission needs a public link to the code (PDT section 2; to be
  confirmed in the official Project Submission Guide).
- This repository is private.
- `@soloft/uds` is private and its licence is `UNLICENSED`.

## Options

| Option | Effect |
| --- | --- |
| A. Make this repository public; keep UDS as a private git dependency | Code is public and reviewable. Nobody outside Soloft can install or build the frontend. Recommended. |
| B. Make this repository public and copy UDS into it | The frontend builds for anyone, and the design system is published with it. |
| C. Submit a separate public repository with the backend and a frontend that does not use UDS | Keeps UDS private and everything buildable, at the cost of maintaining two frontends. |
| D. Publish UDS under a licence | Cleanest technically; a business decision about the design system. |

## Needed now

CI and the production image build need read access to `SerdarOklu/soloft-uds`. CI reads a
fine-grained token from the repository secret `UDS_READ_TOKEN` (read-only, Contents, that
one repository). Without it the frontend job fails at its first step with a message that
says so. No secret is committed. Setup steps are in `frontend/README.md`.

## Before the repository is opened

- Choose one of the options above.
- Check the git history for anything that should not be public. UDS itself is not in this
  repository: it is fetched at install time.

## Licence

This repository has no licence yet. A public repository without one is readable but not
reusable; check whether the challenge rules ask for an open-source licence.
