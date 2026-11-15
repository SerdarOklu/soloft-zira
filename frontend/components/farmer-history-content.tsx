import { Alert, Badge } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { MeadowBanner } from '@/components/illustrations';
import { LineChart } from '@/components/line-chart';
import { Link } from '@/i18n/navigation';
import { api } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/format';
import type { FieldMemory, FieldOut } from '@/lib/types';

const STATE_TONE = { cropped: 'success', fallow: 'neutral', unknown: 'warning' } as const;
const LEVEL_TONE = { high: 'success', medium: 'warning', low: 'danger' } as const;

/**
 * The farmer's view of Field Memory: cropped or fallow in each recent season, from the
 * satellite NDVI. Read only: fetching and confirming belong to the agronomist.
 */
export async function FarmerHistoryContent({ params }: { params: { field?: string; source?: string } }) {
  const [t, locale, fields] = await Promise.all([
    getTranslations('fieldMemory'),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);
  const screen = await getTranslations('screens.myHistory');
  const number = (value: number | null, digits = 2) => formatNumber(value, locale, digits);

  const banner = (
    <header className="zira-farm-banner">
      <MeadowBanner />
      <div>
        <h1 className="zira-farm-title">{screen('title')}</h1>
        <p className="zira-farm-lede">{screen('description')}</p>
      </div>
    </header>
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack zira-farmer zira-farm">
        {banner}
        <p className="zira-farm-card">{(await getTranslations('farmerView'))('noFields')}</p>
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  const source = ['modis', 'landsat'].includes(params.source ?? '') ? params.source : 'auto';
  const memory = await api<FieldMemory>(
    `/fields/${encodeURIComponent(field.id)}/field-memory?source=${source}`,
  );
  const hasData = memory.coverage.observations > 0;
  const unknownCount = memory.seasons.filter(
    (season) => (season.confirmed_state ?? season.detected_state) === 'unknown',
  ).length;
  const monthYear = (iso: string) =>
    new Intl.DateTimeFormat(locale, { month: 'short', year: '2-digit', timeZone: 'UTC' }).format(
      new Date(`${iso}T00:00:00Z`),
    );

  return (
    <div className="zira-stack zira-farmer zira-farm">
      {banner}

      {fields.length > 1 && (
        <nav className="zira-farm-tabs" aria-label={t('form.field')}>
          {fields.map((candidate) => (
            <Link
              key={candidate.id}
              href={`/field-memory?field=${candidate.id}`}
              aria-current={candidate.id === field.id ? 'page' : undefined}
            >
              {candidate.name}
            </Link>
          ))}
        </nav>
      )}

      {!hasData ? (
        <p className="zira-farm-card">{t('none')}</p>
      ) : (
        <>
          {memory.provisional && (
            <Alert tone="warning" title={t('provisional.title')}>
              {t('provisional.body', { value: number(memory.threshold) })}
            </Alert>
          )}
          {unknownCount > 0 && <Alert tone="info">{t('unknownWarning', { count: unknownCount })}</Alert>}

          <section className="zira-farm-card" aria-labelledby="seasons-title">
            <h2 id="seasons-title">{t('seasons.title')}</h2>
            <ul className="zira-farm-seasons">
              {memory.seasons.map((season) => {
                const state = season.confirmed_state ?? season.detected_state;
                return (
                  <li key={season.season} className={`zira-farm-season zira-farm-season--${state}`}>
                    <strong>{season.season}</strong>
                    <Badge tone={STATE_TONE[state]}>{t(`states.${state}`)}</Badge>
                    {season.confidence_level && (
                      <Badge tone={LEVEL_TONE[season.confidence_level]}>
                        {t(`levels.${season.confidence_level}`)}
                      </Badge>
                    )}
                    <span className="zira-farm-meta">
                      {t('columns.images')}: {season.good_observations} / {season.total_observations}
                    </span>
                    {season.peak_ndvi !== null && (
                      <span className="zira-farm-meta">
                        {t('columns.peak')}: {number(season.peak_ndvi)} · {formatDate(season.peak_date, locale)}
                      </span>
                    )}
                    {season.confirmed_by && (
                      <span className="zira-farm-meta">{t(`confirmed.by.${season.confirmed_by}`)}</span>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="zira-farm-meta">
              {t('confirmed.summary', { count: memory.confirmed_count, total: memory.seasons.length })}
            </p>
          </section>

          <section className="zira-farm-card" aria-labelledby="ndvi-title">
            <h2 id="ndvi-title">{t('chart.title')}</h2>
            <p className="zira-farm-meta">
              {t('usedSource', {
                source: t(`sources.${memory.source}`),
                landsat: memory.available_sources.landsat ?? 0,
                modis: memory.available_sources.modis ?? 0,
              })}
            </p>
            <p className="zira-farm-meta">
              {t('coverage', {
                count: memory.coverage.observations,
                good: memory.coverage.good,
                from: formatDate(memory.coverage.first_date, locale),
                to: formatDate(memory.coverage.last_date, locale),
              })}
            </p>
            <LineChart
              dates={memory.series.map((point) => point.date)}
              yMax={1}
              ariaLabel={t('chart.aria')}
              formatDate={monthYear}
              formatTick={(value) => number(value, 1)}
              series={[
                {
                  label: t('chart.legend'),
                  values: memory.series.map((point) => point.ndvi),
                  tone: 'primary',
                },
                {
                  label: t('chart.thresholdLegend', { value: number(memory.threshold) }),
                  values: memory.series.map(() => memory.threshold),
                  tone: 'muted',
                  dashed: true,
                },
              ]}
            />
            <div className="zira-legend">
              <span>
                <span className="zira-legend-swatch" />
                {t('chart.legend')}
              </span>
              <span>
                <span className="zira-legend-swatch zira-legend-swatch--muted" />
                {t('chart.thresholdLegend', { value: number(memory.threshold) })}
              </span>
            </div>
            <p className="zira-farm-meta">{t('source')}</p>
          </section>
        </>
      )}

      <p className="zira-farm-meta">{t('limits')}</p>
    </div>
  );
}
