import { NextResponse } from 'next/server';

import { passwordlessSignIn, readStrings } from '@/lib/sign-in';

/** Farmer sign-in, step 2: the code from WhatsApp opens the session. */
export async function POST(request: Request) {
  const body = await readStrings(request, ['phone', 'code']);
  if (!body) return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  return passwordlessSignIn('code/verify', body, 'invalid_code');
}
