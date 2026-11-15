import { NextResponse } from 'next/server';

/**
 * The browser-side map settings. The Google Maps key is read from the server environment at run
 * time (no rebuild to change it). It is a public key by design: restrict it to this site's address
 * and to the Map Tiles API in the Google Cloud console. Without it the map still works.
 */
export function GET() {
  return NextResponse.json(
    { googleMapsKey: process.env.GOOGLE_MAPS_API_KEY?.trim() || null },
    { headers: { 'Cache-Control': 'no-store' } },
  );
}
