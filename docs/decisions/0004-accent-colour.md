# 0004: Product accent

**Status:** Accepted: khaki green. The exact value is open and blocks Phase 1.

## Decision

Zira's accent is khaki green (decided by the product owner, 14 November 2026). In UDS a
product sets exactly one variable:

```css
[data-uds-theme='zira'] { --uds-primary: <approved value>; }
```

Hover, active, subtle, border and focus tokens derive from it. Status colours (success,
warning, danger) keep their meaning and never follow the accent.

## Open: the exact value

"Khaki green" is a name, not a value, and UDS forbids picking one without approval. The
accent carries white text on primary buttons, so contrast against white matters. For
reference, the Soloft Client accent `#2457FF` has a contrast of 5.41 against white.

| Candidate | Contrast with white text | Contrast on the dark surface `#111111` | Note |
| --- | --- | --- | --- |
| `#5E6B3B` | 5.77 | 3.28 | Closest in contrast to the Client accent; recommended |
| `#6B7A45` | 4.67 | 4.04 | Lighter; just above the 4.5 threshold for body text |
| `#4F5D2F` | 7.14 | 2.64 | Darker; weak on dark surfaces |
| `#C3B091` (web "khaki") | 2.11 | 8.94 | Too light for white text |

Until a value is approved the frontend keeps the Client accent.
