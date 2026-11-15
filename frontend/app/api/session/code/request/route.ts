import { NextResponse } from 'next/server';

import { readStrings, requestCode } from '@/lib/sign-in';

/** Farmer sign-in, step 1: send a code to the phone number's WhatsApp. */
export async function POST(request: Request) {
  const body = await readStrings(request, ['phone']);
  if (!body) return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  return requestCode(body.phone);
}
