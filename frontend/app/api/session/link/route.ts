import { NextResponse } from 'next/server';

import { passwordlessSignIn, readStrings } from '@/lib/sign-in';

/** Farmer sign-in with the one-time link a cooperative handed over. */
export async function POST(request: Request) {
  const body = await readStrings(request, ['token']);
  if (!body) return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  return passwordlessSignIn('link/redeem', body, 'invalid_link');
}
