# 0005: Repository visibility and the private UDS dependency

**Status:** Open. Blocks the Space Apps submission, not development.

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

## Also needed whatever is chosen

From Phase 1 on, CI and the production image build need read access to
`SerdarOklu/soloft-uds`: a read-only deploy key or a fine-grained token stored as a
repository secret. No secret is committed.

## Licence

This repository has no licence yet. A public repository without one is readable but not
reusable; check whether the challenge rules ask for an open-source licence.
