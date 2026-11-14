import 'server-only';

import { cookies } from 'next/headers';

import { BACKEND_URL, SESSION_COOKIE } from './config';
import { isRole, type SessionUser } from './roles';

/**
 * The signed-in user, or null. Asks the backend on every call, so a deactivated
 * account or an expired token loses access at once.
 */
export async function getSessionUser(): Promise<SessionUser | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    });
    if (!response.ok) return null;
    const user: unknown = await response.json();
    return isSessionUser(user) ? user : null;
  } catch {
    // Backend unreachable: treat as signed out rather than crash the page.
    return null;
  }
}

function isSessionUser(value: unknown): value is SessionUser {
  if (typeof value !== 'object' || value === null) return false;
  const user = value as Record<string, unknown>;
  return (
    typeof user.id === 'string' &&
    typeof user.email === 'string' &&
    typeof user.name === 'string' &&
    isRole(user.role)
  );
}
