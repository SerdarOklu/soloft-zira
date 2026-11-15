import { NextResponse } from 'next/server';

import { BACKEND_URL } from '@/lib/config';
import { passwordlessSignIn, readStrings } from '@/lib/sign-in';

/** Which roles can be entered without a password (empty unless the server turned demo mode on). */
export async function GET() {
  try {
    const backend = await fetch(`${BACKEND_URL}/api/v1/auth/demo/roles`, { cache: 'no-store' });
    if (!backend.ok) return NextResponse.json({ enabled: false, roles: [] });
    return NextResponse.json(await backend.json());
  } catch {
    return NextResponse.json({ enabled: false, roles: [] });
  }
}

/** Demo sign-in: choose a role, no password. The backend refuses unless demo mode is on. */
export async function POST(request: Request) {
  const body = await readStrings(request, ['role']);
  if (!body) return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  return passwordlessSignIn('demo/login', body, 'demo_unavailable');
}
