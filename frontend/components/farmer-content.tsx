import { Alert, Badge, PageHeader, Section } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { api } from '@/lib/api';
import { formatDate, formatDateTime, formatNumber } from '@/lib/format';
import type { FarmerSummary } from '@/lib/types';

/** What a farmer sees: the water in their own field, and the messages that were sent to them. */
export async function FarmerContent() {
  const [t, locale, summary] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FarmerSummary>('/farmer/summary'),
  ]);
  const number = (value: number, digits = 0) => formatNumber(value, locale, digits);

  return (
    <div className="zira-stack zira-farmer">
      <PageHeader title={t('farmerView.hello', { name: summary.name })} description={t('screens.farmer.description')} />

      {summary.fields.length === 0 && <Alert tone="info">{t('farmerView.noFields')}</Alert>}

      {summary.fields.map((field) => (
        <Section key={field.id} title={field.name}>
          <div className="zira-stack">
            {field.water ? (
              <>
                <p className="zira-farmer-figure">
                  {t('farmerView.mm', { value: number(field.water.storage_mm) })}
                </p>
                <p>
                  {t('farmerView.waterTitle')} ·{' '}
                  {t('farmerView.ofCapacity', {
                    percent: number(field.water.fill_fraction * 100),
                    capacity: number(field.water.taw_mm),
                  })}
                </p>
                <p className="zira-muted">
                  {t('farmerView.range', {
                    low: number(field.water.low_mm),
                    high: number(field.water.high_mm),
                  })}{' '}
                  · {t('farmerView.asOf', { date: formatDate(field.water.date, locale) })}
                </p>
                <p>
                  <Badge tone={field.mode === 'sensor' ? 'success' : 'neutral'}>
                    {t(`farmerView.mode.${field.mode}`)}
                  </Badge>
                </p>
              </>
            ) : (
              <Alert tone="warning">
                {t(
                  field.water_problem && t.has(`farmerView.problems.${field.water_problem}`)
                    ? `farmerView.problems.${field.water_problem}`
                    : 'farmerView.problems.generic',
                )}
              </Alert>
            )}
            {field.last_weather_date && (
              <p className="zira-muted">
                {t('farmerView.lastData', { date: formatDate(field.last_weather_date, locale) })}
              </p>
            )}
          </div>
        </Section>
      ))}

      <Section title={t('farmerView.messagesTitle')}>
        {summary.messages.length === 0 ? (
          <p>{t('farmerView.noMessages')}</p>
        ) : (
          <ul className="zira-draft-list">
            {summary.messages.map((message) => (
              <li key={message.id} className="zira-farmer-message">
                <p className="zira-draft-head">
                  <strong>
                    {t.has(`farmerView.events.${message.event_type}`)
                      ? t(`farmerView.events.${message.event_type}`)
                      : message.event_type}
                  </strong>
                  <span className="zira-muted">
                    {message.sent_at
                      ? t('farmerView.sentAt', { date: formatDateTime(message.sent_at, locale) })
                      : formatDate(message.event_date, locale)}
                  </span>
                </p>
                <div className="zira-bubble">{message.body}</div>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <p className="zira-statement">{t('farmerView.support')}</p>
    </div>
  );
}
