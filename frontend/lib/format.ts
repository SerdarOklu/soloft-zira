/** Number and date formatting for the interface. Missing values show as an em dash. */

export const MISSING = '—';

/** Timestamps are shown in the time zone of the farms: the server runs in UTC. */
const DISPLAY_TIME_ZONE = 'Europe/Istanbul';

export function formatNumber(
  value: number | null | undefined,
  locale: string,
  digits = 1,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return MISSING;
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/** A calendar date such as "2024-01-31". Read as UTC so no time zone can move the day. */
export function formatDate(iso: string | null | undefined, locale: string): string {
  if (!iso) return MISSING;
  const date = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return MISSING;
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: 'UTC' }).format(date);
}

/** A moment in time (an ISO timestamp with offset). */
export function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) return MISSING;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return MISSING;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: DISPLAY_TIME_ZONE,
  }).format(date);
}
