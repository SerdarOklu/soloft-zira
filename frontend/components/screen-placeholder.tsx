'use client';

import { PageHeader, Placeholder } from '@soloft/uds';
import { useTranslations } from 'next-intl';

import { SCREENS, type ScreenKey } from '@/lib/nav';

/** A screen whose content arrives in a later phase: its title, purpose and what it will hold. */
export function ScreenPlaceholder({ screen }: { screen: ScreenKey }) {
  const t = useTranslations();
  const phase = SCREENS.find((candidate) => candidate.key === screen)?.phase ?? 0;
  const items = t.raw(`screens.${screen}.items`) as string[];

  return (
    <>
      <PageHeader
        title={t(`screens.${screen}.title`)}
        description={t(`screens.${screen}.description`)}
      />
      <Placeholder
        badge={t('placeholder.badge', { phase })}
        note={t('placeholder.note', { phase })}
        items={items}
      />
      <p className="zira-statement">{t('app.supportStatement')}</p>
    </>
  );
}
