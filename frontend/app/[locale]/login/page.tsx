import { setRequestLocale } from 'next-intl/server';

import { LoginScreen } from '@/components/login-screen';
import { redirect } from '@/i18n/navigation';
import { getSessionUser } from '@/lib/session';

export default async function LoginPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  if (await getSessionUser()) redirect({ href: '/', locale });
  return <LoginScreen />;
}
