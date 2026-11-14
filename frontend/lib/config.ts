/** Server-side address of the FastAPI backend. Never sent to the browser. */
export const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

/** httpOnly cookie holding the access token. */
export const SESSION_COOKIE = 'zira_session';

/**
 * The session cookie is sent over HTTPS only in production. Set
 * SESSION_COOKIE_SECURE=false to try a production build over plain http on localhost.
 */
export function sessionCookieSecure(): boolean {
  const override = process.env.SESSION_COOKIE_SECURE;
  if (override === 'true') return true;
  if (override === 'false') return false;
  return process.env.NODE_ENV === 'production';
}
/** Readable preference cookies, written by the browser. */
export const THEME_COOKIE = 'zira_theme';
export const SIDEBAR_COOKIE = 'zira_sidebar';

export type Mode = 'light' | 'dark';

export function parseMode(value: string | undefined): Mode {
  return value === 'dark' ? 'dark' : 'light';
}

export function parseSidebarCollapsed(value: string | undefined): boolean {
  return value === 'collapsed';
}
