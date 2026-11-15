import { Badge } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { FieldIllustration, MeadowBanner } from '@/components/illustrations';
import { api } from '@/lib/api';
import { formatNumber } from '@/lib/format';
import type { FieldOut } from '@/lib/types';

/** The farmer's fields as cards. Read only: a farmer neither adds nor edits a field. */
export async function FarmerFieldsContent() {
  const [t, locale, fields] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);

  return (
    <div className="zira-stack zira-farmer zira-farm">
      <header className="zira-farm-banner">
        <MeadowBanner />
        <div>
          <h1 className="zira-farm-title">{t('screens.myFields.title')}</h1>
          <p className="zira-farm-lede">{t('screens.myFields.description')}</p>
        </div>
      </header>

      {fields.length === 0 && <p className="zira-farm-card">{t('farmerView.noFields')}</p>}

      {fields.map((field) => {
        const soil =
          field.soil_texture && t.has(`soils.${field.soil_texture}`)
            ? t(`soils.${field.soil_texture}`)
            : field.soil_texture;
        const rows: [string, string | null][] = [
          [t('fields.columns.region'), field.region],
          [
            t('fields.columns.area'),
            field.area_ha === null ? null : `${formatNumber(field.area_ha, locale, 1)} ha`,
          ],
          [t('fields.columns.soil'), soil],
          [
            t('fields.columns.regime'),
            field.water_regime ? t(`regimes.${field.water_regime}`) : null,
          ],
        ];
        return (
          <section key={field.id} className="zira-farm-card" aria-labelledby={`field-${field.id}`}>
            <div className="zira-farm-fieldhead">
              <FieldIllustration />
              <h2 id={`field-${field.id}`}>{field.name}</h2>
            </div>
            <dl className="zira-farm-facts">
              {rows.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value ?? '—'}</dd>
                </div>
              ))}
            </dl>
            <p>
              {field.weather_days > 0 ? (
                <Badge tone="success" dot>
                  {t('fields.dataDays', { days: field.weather_days })}
                </Badge>
              ) : (
                <Badge tone="warning" dot>
                  {t('fields.dataMissing')}
                </Badge>
              )}
            </p>
          </section>
        );
      })}
    </div>
  );
}
