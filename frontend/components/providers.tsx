'use client';

import { UdsProvider } from '@soloft/uds';
import type { ReactNode } from 'react';

import { Link } from '@/i18n/navigation';

// Every link UDS renders goes through the locale-aware router link.
export function Providers({ children }: { children: ReactNode }) {
  return <UdsProvider linkComponent={Link}>{children}</UdsProvider>;
}
