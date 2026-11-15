import { ClipboardList, CloudRain, Droplets, MapPinned, Sprout, TriangleAlert } from 'lucide-react';
import type { ReactNode } from 'react';
import { getLocale, getTranslations } from 'next-intl/server';

import { MeadowBanner } from '@/components/illustrations';
import { api } from '@/lib/api';
import { formatDate, formatDateTime } from '@/lib/format';
import type { MessageDraft } from '@/lib/types';

const ICONS: Record<string, ReactNode> = {
  decision: <Sprout />,
  heavy_rain: <CloudRain />,
  leaching: <Droplets />,
  stress: <TriangleAlert />,
  harvest: <ClipboardList />,
  card: <MapPinned />,
};

/**
 * What Zira sent to the farmer, after an agronomist approved it. The API gives a farmer only
 * messages with status "sent", so an unapproved draft never reaches this screen.
 */
export async function FarmerMessagesContent() {
  const [t, locale, messages] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<MessageDraft[]>('/messages'),
  ]);
  const sent = messages.filter((message) => message.status === 'sent');

  return (
    <div className="zira-stack zira-farmer zira-farm">
      <header className="zira-farm-banner">
        <MeadowBanner />
        <div>
          <h1 className="zira-farm-title">{t('screens.myMessages.title')}</h1>
          <p className="zira-farm-lede">{t('screens.myMessages.description')}</p>
        </div>
      </header>

      {sent.length === 0 ? (
        <p className="zira-farm-card">{t('farmerView.noMessages')}</p>
      ) : (
        <ul className="zira-farm-messages">
          {sent.map((message) => (
            <li key={message.id} className="zira-farm-card">
              <div className="zira-farm-message-head">
                <span className="zira-farm-message-icon" aria-hidden="true">
                  {ICONS[message.event_type] ?? <ClipboardList />}
                </span>
                <div>
                  <h2>
                    {t.has(`farmerView.events.${message.event_type}`)
                      ? t(`farmerView.events.${message.event_type}`)
                      : message.event_type}
                  </h2>
                  <p className="zira-farm-meta">
                    {message.field_name} ·{' '}
                    {message.sent_at
                      ? t('farmerView.sentAt', { date: formatDateTime(message.sent_at, locale) })
                      : formatDate(message.event_date, locale)}
                  </p>
                </div>
              </div>
              <div className="zira-bubble">{message.body}</div>
            </li>
          ))}
        </ul>
      )}

      <p className="zira-statement">{t('farmerView.support')}</p>
    </div>
  );
}
