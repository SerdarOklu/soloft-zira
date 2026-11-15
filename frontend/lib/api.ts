import 'server-only';

import { cookies } from 'next/headers';

import { BACKEND_URL, SESSION_COOKIE } from './config';

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    /** The `code` and details of a refusal the backend explains, such as a missing date. */
    readonly detail: { code?: string; [key: string]: unknown } | null = null,
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
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail =
      body && typeof body.detail === 'object' && body.detail !== null
        ? (body.detail as ApiError['detail'])
        : null;
    throw new ApiError(response.status, `${path} answered HTTP ${response.status}`, detail);
  }
  return (await response.json()) as T;
}
