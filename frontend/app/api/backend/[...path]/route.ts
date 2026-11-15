import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { BACKEND_URL, SESSION_COOKIE } from '@/lib/config';
import { backendPath } from '@/lib/proxy';

/**
 * The browser's way to the backend. The access token lives in an httpOnly cookie, so
 * scripts on the page cannot send it; this route adds it. Only the fields and messages APIs are
 * forwarded (see lib/proxy.ts) and the backend still checks the role on every call.
 */
async function forward(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const target = backendPath((await context.params).path);
  if (!target) return NextResponse.json({ error: 'not_found' }, { status: 404 });

  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const hasBody = request.method === 'POST' || request.method === 'PATCH';
  // A cross-site form cannot send JSON, so this closes the last gap beside SameSite=Lax.
  if (hasBody && !request.headers.get('content-type')?.includes('application/json')) {
    return NextResponse.json({ error: 'invalid_request' }, { status: 415 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}${target}${new URL(request.url).search}`, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
      },
      body: hasBody ? await request.text() : undefined,
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ error: 'backend_unreachable' }, { status: 502 });
  }

  return new NextResponse(upstream.status === 204 ? null : upstream.body, {
    status: upstream.status,
    headers: { 'Content-Type': upstream.headers.get('content-type') ?? 'application/json' },
  });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
