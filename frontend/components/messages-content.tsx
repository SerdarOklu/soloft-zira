import { PageHeader } from '@soloft/uds';
import { getTranslations } from 'next-intl/server';

import { MessagesQueue } from '@/components/messages-queue';
import { api } from '@/lib/api';
import { getSessionUser } from '@/lib/session';
import type { FieldOut, GatewayStatus, MessageDraft } from '@/lib/types';

/** The autumn whose decision day is the most recent one that has already passed. */
function currentDecisionYear(now: Date): number {
  return now.getUTCMonth() >= 9 ? now.getUTCFullYear() : now.getUTCFullYear() - 1;
}

/** WhatsApp drafts waiting for the agronomist, and what already went out. */
export async function MessagesContent() {
  const [t, user, drafts, fields, gateway] = await Promise.all([
    getTranslations(),
    getSessionUser(),
    api<MessageDraft[]>('/messages'),
    api<FieldOut[]>('/fields'),
    api<GatewayStatus>('/messages/gateway'),
  ]);

  return (
    <div className="zira-stack">
      <PageHeader title={t('screens.messages.title')} description={t('screens.messages.description')} />
      <MessagesQueue
        drafts={drafts}
        fields={fields.map(({ id, name }) => ({ id, name }))}
        gatewayConfigured={gateway.configured}
        defaultYear={currentDecisionYear(new Date())}
        canReview={user?.role === 'admin' || user?.role === 'agronomist'}
      />
    </div>
  );
}
