import type { ReactNode } from 'react';

import { ScreenPlaceholder } from '@/components/screen-placeholder';
import { ForbiddenScreen } from '@/components/system-screens';
import { canOpen, type ScreenKey } from '@/lib/nav';
import { getSessionUser } from '@/lib/session';

/**
 * Renders a screen only for roles allowed to open it. The menu already hides the
 * others; this covers a typed-in address. A screen whose phase has arrived passes its
 * content as children; the others still show the placeholder.
 */
export async function GuardedScreen({
  screen,
  children,
}: {
  screen: ScreenKey;
  children?: ReactNode;
}) {
  const user = await getSessionUser();
  if (!user || !canOpen(user.role, screen)) return <ForbiddenScreen />;
  return children ?? <ScreenPlaceholder screen={screen} />;
}
