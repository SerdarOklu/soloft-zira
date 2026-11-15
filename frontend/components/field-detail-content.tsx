import { Button, DescriptionList, PageHeader, Section } from '@soloft/uds';
import { notFound } from 'next/navigation';
import { getLocale, getTranslations } from 'next-intl/server';

import { FieldMap } from '@/components/field-map';
import { WeatherPanel } from '@/components/weather-panel';
import { ApiError, api } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/format';
import type { FieldOut, WeatherSummary } from '@/lib/types';

export async function FieldDetailContent({ id }: { id: string }) {
  const path = `/fields/${encodeURIComponent(id)}`;
  let field: FieldOut;
  let weather: WeatherSummary;
  try {
    [field, weather] = await Promise.all([
      api<FieldOut>(path),
      api<WeatherSummary>(`${path}/weather/summary`),
    ]);
  } catch (error) {
    // Unknown, malformed or someone else's field: all look the same from here.
    if (error instanceof ApiError && (error.status === 404 || error.status === 422)) notFound();
    throw error;
  }

  const [t, locale] = await Promise.all([getTranslations(), getLocale()]);
  const soil = field.soil_texture;

  return (
    <div className="zira-stack">
      <PageHeader
        title={field.name}
        description={field.code}
        actions={
          <Button href="/fields" variant="secondary">
            {t('fields.back')}
          </Button>
        }
      />

      <div className="zira-grid-2">
        <Section title={t('fields.detail.profile')}>
          <DescriptionList
            variant="compact"
            items={[
              [t('fields.detail.code'), field.code],
              [t('fields.detail.region'), field.region],
              [
                t('fields.detail.area'),
                field.area_ha === null
                  ? null
                  : t('fields.detail.areaValue', { value: formatNumber(field.area_ha, locale, 1) }),
              ],
              [
                t('fields.detail.elevation'),
                field.elevation_m === null
                  ? t('fields.detail.elevationPending')
                  : t('fields.detail.elevationValue', {
                      value: formatNumber(field.elevation_m, locale, 0),
                    }),
              ],
              [
                t('fields.detail.soil'),
                soil && t.has(`soils.${soil}`) ? t(`soils.${soil}`) : soil,
              ],
              [
                t('fields.detail.regime'),
                field.water_regime ? t(`regimes.${field.water_regime}`) : null,
              ],
              [
                t('fields.detail.location'),
                field.centroid
                  ? `${formatNumber(field.centroid.lat, locale, 4)}, ${formatNumber(field.centroid.lon, locale, 4)}`
                  : null,
              ],
              [t('fields.detail.created'), formatDate(field.created_at, locale)],
            ]}
          />
        </Section>

        <FieldMap mode="view" ariaLabel={t('fields.detail.mapAria')} geometry={field.geometry} />
      </div>

      <WeatherPanel fieldId={field.id} initial={weather} />

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
