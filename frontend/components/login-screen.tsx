'use client';

import { AuthHeader, AuthLayout, Button, Field, Input, LoginForm, VerificationForm } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { useRouter } from '@/i18n/navigation';

import { AuthLogo } from './brand';

const KNOWN_ERRORS = ['invalid_credentials', 'backend_unreachable'] as const;
type KnownError = (typeof KNOWN_ERRORS)[number];
type Way = 'farmer' | 'staff';
const RESEND_SECONDS = 30;

/**
 * Sign-in. A farmer needs no password: a code comes to their WhatsApp. Staff keep the password.
 * The two buttons only choose how to prove who you are; the role always comes from the account.
 */
export function LoginScreen() {
  const t = useTranslations('login');
  const app = useTranslations('app');
  const locale = useLocale();
  const router = useRouter();
  const [way, setWay] = useState<Way>('farmer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [phone, setPhone] = useState('');
  const [codeSent, setCodeSent] = useState(false);

  const enter = () => {
    router.replace('/');
    router.refresh();
  };
  const choose = (next: Way) => {
    setWay(next);
    setError(undefined);
  };

  const signIn = async ({ email, password }: { email: string; password: string }) => {
    setLoading(true);
    setError(undefined);
    try {
      const response = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (response.ok) return enter();
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      const code = KNOWN_ERRORS.includes(body.error as KnownError)
        ? (body.error as KnownError)
        : 'generic';
      setError(t(`errors.${code}`));
    } catch {
      setError(t('errors.backend_unreachable'));
    }
    setLoading(false);
  };

  const sendCode = async () => {
    setError(undefined);
    if (phone.replace(/\D/g, '').length < 10) {
      setError(t('errors.invalid_phone'));
      return false;
    }
    setLoading(true);
    try {
      const response = await fetch('/api/session/code/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      if (response.ok) return true;
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      setError(
        body.error === 'code_unavailable'
          ? t('errors.code_unavailable')
          : body.error === 'invalid_phone'
            ? t('errors.invalid_phone')
            : t('errors.backend_unreachable'),
      );
    } catch {
      setError(t('errors.backend_unreachable'));
    } finally {
      setLoading(false);
    }
    return false;
  };

  const onPhone = async (event: FormEvent) => {
    event.preventDefault();
    if (await sendCode()) setCodeSent(true);
  };

  const verify = async ({ code }: { code: string }) => {
    setLoading(true);
    setError(undefined);
    try {
      const response = await fetch('/api/session/code/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      });
      if (response.ok) return enter();
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      setError(body.error === 'backend_unreachable' ? t('errors.backend_unreachable') : t('errors.invalid_code'));
    } catch {
      setError(t('errors.backend_unreachable'));
    }
    setLoading(false);
  };

  const udsLocale = locale === 'en' ? 'en' : 'tr';

  return (
    <AuthLayout icon={<AuthLogo name={app('name')} />}>
      <AuthHeader title={t('welcome')} description={t('welcomeLead')} />

      <div className="zira-actions zira-way" role="group" aria-label={t('wayLabel')}>
        {(['farmer', 'staff'] as const).map((key) => (
          <Button
            key={key}
            type="button"
            variant={way === key ? 'primary' : 'secondary'}
            aria-pressed={way === key}
            onClick={() => choose(key)}
          >
            {t(`ways.${key}`)}
          </Button>
        ))}
      </div>

      {way === 'staff' ? (
        <LoginForm
          locale={udsLocale}
          title={t('staffTitle')}
          description={t('description')}
          onSubmit={signIn}
          loading={loading}
          error={error}
        />
      ) : codeSent ? (
        <VerificationForm
          locale={udsLocale}
          length={6}
          inputMode="numeric"
          title={t('codeTitle')}
          description={t('codeDescription', { phone })}
          copy={{ verifyCodeLabel: t('codeLabel'), verifySubmit: t('codeSubmit'), verifyResend: t('resend') }}
          onSubmit={verify}
          onResend={() => void sendCode()}
          resendCooldown={RESEND_SECONDS}
          loading={loading}
          error={error}
          footer={
            <div className="zira-stack">
              <p className="zira-muted">{t('noCode')}</p>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setCodeSent(false);
                  setError(undefined);
                }}
              >
                {t('changeNumber')}
              </Button>
            </div>
          }
        />
      ) : (
        <form className="zira-stack" onSubmit={onPhone} noValidate>
          <AuthHeader title={t('phoneTitle')} description={t('phoneDescription')} />
          {error && <p role="alert">{error}</p>}
          <Field label={t('phoneLabel')}>
            <Input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder={t('phonePlaceholder')}
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              maxLength={32}
              required
            />
          </Field>
          <Button type="submit" size="lg" loading={loading}>
            {t('sendCode')}
          </Button>
          <p className="zira-muted">{t('linkHint')}</p>
        </form>
      )}
    </AuthLayout>
  );
}
