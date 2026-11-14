import { cookies } from 'next/headers';
import { setRequestLocale } from 'next-intl/server';
import type { ReactNode } from 'react';

import { ConsoleShell } from '@/components/console-shell';
import { redirect } from '@/i18n/navigation';
import { parseMode, parseSidebarCollapsed, SIDEBAR_COOKIE, THEME_COOKIE } from '@/lib/config';
import { getSessionUser } from '@/lib/session';

export default async function ConsoleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const user = await getSessionUser();
  if (!user) return redirect({ href: '/login', locale });

  const store = await cookies();
  return (
    <ConsoleShell
      user={user}
      defaultMode={parseMode(store.get(THEME_COOKIE)?.value)}
      defaultCollapsed={parseSidebarCollapsed(store.get(SIDEBAR_COOKIE)?.value)}
    >
      {children}
    </ConsoleShell>
  );
}
