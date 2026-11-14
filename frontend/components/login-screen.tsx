'use client';

import { AuthLayout, LoginForm } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useState } from 'react';

import { useRouter } from '@/i18n/navigation';

const KNOWN_ERRORS = ['invalid_credentials', 'backend_unreachable'] as const;
type KnownError = (typeof KNOWN_ERRORS)[number];

export function LoginScreen() {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const signIn = async ({ email, password }: { email: string; password: string }) => {
    setLoading(true);
    setError(undefined);
    try {
      const response = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (response.ok) {
        router.replace('/');
        router.refresh();
        return;
      }
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      const code = KNOWN_ERRORS.includes(body.error as KnownError)
        ? (body.error as KnownError)
        : 'generic';
      setError(t(`login.errors.${code}`));
    } catch {
      setError(t('login.errors.backend_unreachable'));
    }
    setLoading(false);
  };

  return (
    <AuthLayout
      icon={<span className="zira-wordmark zira-wordmark--auth">{t('app.name')}</span>}
    >
      <LoginForm
        locale={locale === 'en' ? 'en' : 'tr'}
        description={t('login.description')}
        onSubmit={signIn}
        loading={loading}
        error={error}
      />
    </AuthLayout>
  );
}
