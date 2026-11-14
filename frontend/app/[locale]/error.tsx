'use client';

import { ServerErrorScreen } from '@/components/system-screens';

export default function ErrorBoundary({ reset }: { error: Error; reset: () => void }) {
  return <ServerErrorScreen onRetry={reset} />;
}
