/**
 * The browser reaches the backend only through /api/backend/*, which adds the token from
 * the httpOnly cookie. Only these first path segments are forwarded, and every segment
 * must be a plain identifier: no dots, slashes or encoded tricks.
 */
const SEGMENT = /^[A-Za-z0-9_-]+$/;
const ALLOWED_ROOTS = new Set(['fields', 'messages']);

/** The backend path for the proxied segments, or null when they must not be forwarded. */
export function backendPath(segments: string[]): string | null {
  if (segments.length === 0 || !segments.every((segment) => SEGMENT.test(segment))) return null;
  if (!ALLOWED_ROOTS.has(segments[0])) return null;
  return `/api/v1/${segments.join('/')}`;
}
