'use client';

import { AppShell, DropdownItem, DropdownSeparator, ModeToggle, UserMenu } from '@soloft/uds';
import {
  Database,
  Droplets,
  History,
  Languages,
  LayoutDashboard,
  LogOut,
  MapPinned,
  MessageCircle,
  Repeat,
  Settings,
} from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import type { ReactNode } from 'react';

import { usePathname, useRouter } from '@/i18n/navigation';
import { routing } from '@/i18n/routing';
import { SIDEBAR_COOKIE, THEME_COOKIE, type Mode } from '@/lib/config';
import { dockScreensFor, screensFor, type ScreenKey } from '@/lib/nav';
import type { SessionUser } from '@/lib/roles';

import { Wordmark, WordmarkIcon } from './brand';

const ICONS: Record<ScreenKey, ReactNode> = {
  dashboard: <LayoutDashboard />,
  fields: <MapPinned />,
  fieldMemory: <History />,
  waterVault: <Droplets />,
  rotation: <Repeat />,
  messages: <MessageCircle />,
  dataCenter: <Database />,
  settings: <Settings />,
};

const ONE_YEAR = 60 * 60 * 24 * 365;

function writePreference(name: string, value: string) {
  document.cookie = `${name}=${value}; path=/; max-age=${ONE_YEAR}; samesite=lax`;
}

interface ConsoleShellProps {
  user: SessionUser;
  defaultMode: Mode;
  defaultCollapsed: boolean;
  children: ReactNode;
}

export function ConsoleShell({ user, defaultMode, defaultCollapsed, children }: ConsoleShellProps) {
  const t = useTranslations();
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  const nav = screensFor(user.role).map((screen) => ({
    key: screen.key,
    href: screen.href,
    label: t(`nav.${screen.key}`),
    icon: ICONS[screen.key],
    bottom: screen.bottom,
  }));
  // The dock is narrow: it uses short labels.
  const dock = dockScreensFor(user.role).map((screen) => ({
    href: screen.href,
    label: t(`dock.${screen.key}`),
    icon: ICONS[screen.key],
  }));

  const otherLocale = routing.locales.find((candidate) => candidate !== locale) ?? locale;

  const signOut = async () => {
    await fetch('/api/session', { method: 'DELETE' });
    router.replace('/login');
    router.refresh();
  };

  const menu = (
    <>
      <DropdownItem
        icon={<Languages />}
        onSelect={() => router.replace(pathname, { locale: otherLocale })}
      >
        {t('shell.switchLanguage')}
      </DropdownItem>
      <DropdownSeparator />
      <DropdownItem icon={<LogOut />} tone="danger" onSelect={signOut}>
        {t('shell.signOut')}
      </DropdownItem>
    </>
  );

  const name = t('app.name');

  return (
    <AppShell
      nav={nav}
      pathname={pathname}
      brand={{
        href: '/',
        label: t('shell.home'),
        logo: <Wordmark name={name} />,
        icon: <WordmarkIcon name={name} />,
      }}
      labels={{
        mainNavigation: t('shell.mainNavigation'),
        toggleSidebar: t('shell.toggleSidebar'),
        openMenu: t('shell.openMenu'),
        closeMenu: t('shell.closeMenu'),
        dockNav: t('shell.dockNav'),
        dockActions: t('shell.dockActions'),
        dockClose: t('shell.dockClose'),
        skipToContent: t('shell.skipToContent'),
      }}
      header={t('app.tagline')}
      headerActions={
        <ModeToggle
          defaultMode={defaultMode}
          onModeChange={(mode) => writePreference(THEME_COOKIE, mode)}
          labels={{ toDark: t('shell.toDark'), toLight: t('shell.toLight') }}
        />
      }
      user={
        <UserMenu name={user.name} role={t(`roles.${user.role}`)} label={t('shell.accountMenu')}>
          {menu}
        </UserMenu>
      }
      mobileUser={
        <UserMenu
          variant="glass"
          name={user.name}
          role={t(`roles.${user.role}`)}
          label={t('shell.accountMenu')}
        >
          {menu}
        </UserMenu>
      }
      dock={{ items: dock }}
      defaultCollapsed={defaultCollapsed}
      onCollapsedChange={(collapsed) =>
        writePreference(SIDEBAR_COOKIE, collapsed ? 'collapsed' : 'expanded')
      }
    >
      {children}
    </AppShell>
  );
}
