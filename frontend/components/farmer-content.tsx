import { Alert, Badge } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { DropIllustration, FieldIllustration, MeadowBanner } from '@/components/illustrations';
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
    <div className="zira-stack zira-farmer zira-farm">
      <header className="zira-farm-banner">
        <MeadowBanner />
        <div>
          <h1 className="zira-farm-title">{t('farmerView.hello', { name: summary.name })}</h1>
          <p className="zira-farm-lede">{t('screens.farmer.description')}</p>
        </div>
      </header>

      {summary.fields.length === 0 && <Alert tone="info">{t('farmerView.noFields')}</Alert>}

      {summary.fields.map((field) => {
        const meta = [
          field.region,
          field.area_ha === null ? null : t('farmerView.areaHa', { value: number(field.area_ha, 1) }),
        ].filter(Boolean);
        const percent = field.water ? Math.min(100, Math.max(0, field.water.fill_fraction * 100)) : 0;
        return (
          <section key={field.id} className="zira-farm-card" aria-labelledby={`field-${field.id}`}>
            <div className="zira-farm-fieldhead">
              <FieldIllustration />
              <div>
                <h2 id={`field-${field.id}`}>{field.name}</h2>
                {meta.length > 0 && <p className="zira-farm-meta">{meta.join(' · ')}</p>}
              </div>
            </div>

            {field.water ? (
              <>
                <div className="zira-farm-water">
                  <DropIllustration />
                  <div>
                    <p className="zira-farm-meta">{t('farmerView.waterTitle')}</p>
                    <p className="zira-farm-figure">
                      {t('farmerView.mm', { value: number(field.water.storage_mm) })}
                    </p>
                  </div>
                </div>
                <div
                  className="zira-farm-bar"
                  role="progressbar"
                  aria-label={t('farmerView.fillAria')}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(percent)}
                >
                  <span style={{ width: `${percent}%` }} />
                </div>
                <p>
                  {t('farmerView.ofCapacity', {
                    percent: number(field.water.fill_fraction * 100),
                    capacity: number(field.water.taw_mm),
                  })}
                </p>
                <p>
                  <span className="zira-farm-range">
                    {t('farmerView.range', {
                      low: number(field.water.low_mm),
                      high: number(field.water.high_mm),
                    })}
                  </span>
                </p>
                <p className="zira-farm-meta">
                  {t('farmerView.asOf', { date: formatDate(field.water.date, locale) })}
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
              <p className="zira-farm-meta">
                {t('farmerView.lastData', { date: formatDate(field.last_weather_date, locale) })}
              </p>
            )}
          </section>
        );
      })}

      <section className="zira-farm-card" aria-labelledby="farmer-messages">
        <h2 id="farmer-messages">{t('farmerView.messagesTitle')}</h2>
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
                  <span className="zira-farm-meta">
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
      </section>

      <p className="zira-statement">{t('farmerView.support')}</p>
    </div>
  );
}
