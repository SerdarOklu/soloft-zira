'use client';

import { Button, ForbiddenPage, NotFoundPage, ServerErrorPage } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';

function useUdsLocale(): 'tr' | 'en' {
  return useLocale() === 'en' ? 'en' : 'tr';
}

export function NotFoundScreen({ inline = false }: { inline?: boolean }) {
  const t = useTranslations('system');
  return (
    <NotFoundPage
      locale={useUdsLocale()}
      layout={inline ? 'inline' : 'page'}
      actions={<Button href="/">{t('backHome')}</Button>}
    />
  );
}

export function ForbiddenScreen() {
  const t = useTranslations('system');
  return (
    <ForbiddenPage
      locale={useUdsLocale()}
      layout="inline"
      background="mode"
      actions={<Button href="/">{t('backHome')}</Button>}
    />
  );
}

export function ServerErrorScreen({ onRetry }: { onRetry: () => void }) {
  const t = useTranslations('system');
  return (
    <ServerErrorPage
      locale={useUdsLocale()}
      actions={<Button onClick={onRetry}>{t('retry')}</Button>}
    />
  );
}
