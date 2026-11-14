# 0007: Primary precipitation source

**Status:** Accepted, 14 November 2026

## Decision

`precip_source` selects the one precipitation series that enters the water balance.
It is `power` until the Earth Engine connection works, then `gpm`, with NASA POWER kept as
a cross-check. The two are never added together.

## Why

The NASA integration report prefers GPM as primary; the location and parameter report asks
only that one be chosen. NASA POWER is a single API call and needs no Earth Engine account,
so it unblocks the Water Vault first.
