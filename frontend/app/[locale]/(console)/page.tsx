import { getLocale } from 'next-intl/server';

import { DashboardContent } from '@/components/dashboard-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { redirect } from '@/i18n/navigation';
import { getSessionUser } from '@/lib/session';

export default async function Page() {
  // A farmer has one screen of their own; the overview is for staff.
  const user = await getSessionUser();
  if (user?.role === 'farmer') redirect({ href: '/farmer', locale: await getLocale() });
  return (
    <GuardedScreen screen="dashboard">
      <DashboardContent />
    </GuardedScreen>
  );
}
