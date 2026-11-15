import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';

import { LoginLinkScreen } from '@/components/login-link-screen';
import { redirect } from '@/i18n/navigation';
import { getSessionUser } from '@/lib/session';

// The address carries a secret: never pass it on in a Referer header.
export const metadata: Metadata = { referrer: 'no-referrer' };

export default async function LoginLinkPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ token?: string }>;
}) {
  const [{ locale }, { token }] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  if (await getSessionUser()) redirect({ href: '/', locale });
  return <LoginLinkScreen token={typeof token === 'string' && token ? token : null} />;
}
