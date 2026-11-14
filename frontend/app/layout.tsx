import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Zira',
  description: 'NASA-powered agricultural decision support.',
};

// Phase 1 replaces this layout with the Soloft UDS shell: `data-uds-theme="zira"`,
// `data-uds-mode`, `class="uds-root"` and <UdsProvider>. See docs/decisions/0002.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
