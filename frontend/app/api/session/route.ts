import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BACKEND_URL, SESSION_COOKIE, sessionCookieSecure } from '@/lib/config';

/**
 * Sign in: forwards the credentials to the backend and keeps the access token in an
 * httpOnly cookie, so page scripts never see it.
 */
export async function POST(request: Request) {
  let credentials: { email?: unknown; password?: unknown };
  try {
    credentials = await request.json();
  } catch {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  }
  if (typeof credentials.email !== 'string' || typeof credentials.password !== 'string') {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  }

  let backend: Response;
  try {
    backend = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: credentials.email, password: credentials.password }),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ error: 'backend_unreachable' }, { status: 502 });
  }

  if (backend.status === 401 || backend.status === 422) {
    return NextResponse.json({ error: 'invalid_credentials' }, { status: 401 });
  }
  if (!backend.ok) {
    return NextResponse.json({ error: 'backend_error' }, { status: 502 });
  }

  const body = (await backend.json()) as {
    access_token: string;
    expires_in: number;
    user: unknown;
  };
  (await cookies()).set(SESSION_COOKIE, body.access_token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: sessionCookieSecure(),
    path: '/',
    maxAge: body.expires_in,
  });
  return NextResponse.json({ user: body.user });
}

/** Sign out. */
export async function DELETE() {
  (await cookies()).delete(SESSION_COOKIE);
  return new NextResponse(null, { status: 204 });
}
