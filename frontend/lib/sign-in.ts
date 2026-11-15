import 'server-only';

import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BACKEND_URL, SESSION_COOKIE, sessionCookieSecure } from './config';

/** The shape the backend answers with when a farmer signs in by link or by code. */
interface BackendSession {
  access_token: string;
  expires_in: number;
  user: unknown;
}

/** Reads a JSON body of string fields, or null when it is not one. */
export async function readStrings(request: Request, keys: string[]): Promise<Record<string, string> | null> {
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const out: Record<string, string> = {};
    for (const key of keys) {
      if (typeof body[key] !== 'string') return null;
      out[key] = body[key];
    }
    return out;
  } catch {
    return null;
  }
}

/**
 * Calls a passwordless sign-in endpoint of the backend. On success the access token goes into
 * the same httpOnly cookie the password sign-in uses, so the browser never sees it.
 * `refused` is the error name sent back for a 401 or 422 (the backend does not say which part
 * was wrong, and neither do we).
 */
export async function passwordlessSignIn(
  path: string,
  payload: Record<string, string>,
  refused: string,
): Promise<NextResponse> {
  let backend: Response;
  try {
    backend = await fetch(`${BACKEND_URL}/api/v1/auth/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ error: 'backend_unreachable' }, { status: 502 });
  }
  if (backend.status === 401 || backend.status === 422) {
    return NextResponse.json({ error: refused }, { status: 401 });
  }
  if (!backend.ok) return NextResponse.json({ error: 'backend_error' }, { status: 502 });

  const body = (await backend.json()) as BackendSession;
  (await cookies()).set(SESSION_COOKIE, body.access_token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: sessionCookieSecure(),
    path: '/',
    maxAge: body.expires_in,
  });
  return NextResponse.json({ user: body.user });
}

/** Asks the backend to send a code. It answers alike for every number, and so do we. */
export async function requestCode(phone: string): Promise<NextResponse> {
  try {
    const backend = await fetch(`${BACKEND_URL}/api/v1/auth/code/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
      cache: 'no-store',
    });
    if (backend.status === 503) {
      return NextResponse.json({ error: 'code_unavailable' }, { status: 503 });
    }
    if (backend.status === 422) {
      return NextResponse.json({ error: 'invalid_phone' }, { status: 400 });
    }
    if (!backend.ok) return NextResponse.json({ error: 'backend_error' }, { status: 502 });
    return NextResponse.json({ sent: true }, { status: 202 });
  } catch {
    return NextResponse.json({ error: 'backend_unreachable' }, { status: 502 });
  }
}
