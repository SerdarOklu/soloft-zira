import 'server-only';

import { cookies } from 'next/headers';

import { BACKEND_URL, SESSION_COOKIE } from './config';

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Reads from the backend on behalf of the signed-in user. The token comes from the
 * httpOnly cookie and never reaches the browser. The backend enforces the roles.
 */
export async function api<T>(path: string): Promise<T> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const response = await fetch(`${BACKEND_URL}/api/v1${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${path} answered HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}
