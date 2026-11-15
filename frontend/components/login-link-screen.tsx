'use client';

import { AuthHeader, AuthLayout, AuthMessage, Button } from '@soloft/uds';
import { useTranslations } from 'next-intl';
import { useState } from 'react';

import { Link, useRouter } from '@/i18n/navigation';

import { AuthLogo } from './brand';

/**
 * The page a farmer opens from the one-time link. The link is used only when they tap the
 * button, so a chat app that previews the address does not use it up.
 */
export function LoginLinkScreen({ token }: { token: string | null }) {
  const t = useTranslations('login');
  const app = useTranslations('app');
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const signIn = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const response = await fetch('/api/session/link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      if (response.ok) {
        router.replace('/');
        router.refresh();
        return;
      }
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      setError(body.error === 'backend_unreachable' ? t('errors.backend_unreachable') : t('errors.invalid_link'));
    } catch {
      setError(t('errors.backend_unreachable'));
    }
    setLoading(false);
  };

  return (
    <AuthLayout icon={<AuthLogo name={app('name')} />}>
      {token ? (
        <div className="zira-stack">
          <AuthHeader title={t('linkTitle')} description={t('linkDescription')} />
          {error && (
            <AuthMessage tone="warning" title={t('linkProblem')} description={error} />
          )}
          <Button type="button" size="lg" loading={loading} onClick={signIn}>
            {t('linkSubmit')}
          </Button>
        </div>
      ) : (
        <AuthMessage
          tone="warning"
          title={t('linkProblem')}
          description={t('errors.invalid_link')}
          actions={<Link href="/login">{t('backToLogin')}</Link>}
        />
      )}
    </AuthLayout>
  );
}
