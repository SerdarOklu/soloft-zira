'use client';

import { Button } from '@soloft/uds';

/** Prints the card (the browser can save it as a PDF). */
export function PrintButton({ label }: { label: string }) {
  return (
    <Button type="button" variant="secondary" onClick={() => window.print()}>
      {label}
    </Button>
  );
}
