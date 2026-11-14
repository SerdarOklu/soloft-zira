import { ScreenPlaceholder } from '@/components/screen-placeholder';
import { ForbiddenScreen } from '@/components/system-screens';
import { canOpen, type ScreenKey } from '@/lib/nav';
import { getSessionUser } from '@/lib/session';

/**
 * Renders a screen only for roles allowed to open it. The menu already hides the
 * others; this covers a typed-in address.
 */
export async function GuardedScreen({ screen }: { screen: ScreenKey }) {
  const user = await getSessionUser();
  if (!user || !canOpen(user.role, screen)) return <ForbiddenScreen />;
  return <ScreenPlaceholder screen={screen} />;
}
