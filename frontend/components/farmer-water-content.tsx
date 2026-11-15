import {
  Alert,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { DropIllustration, MeadowBanner, SproutIllustration } from '@/components/illustrations';
import { LineChart } from '@/components/line-chart';
import { Link } from '@/i18n/navigation';
import { ApiError, api } from '@/lib/api';
import { formatDate, formatDateTime, formatNumber } from '@/lib/format';
import type { CropOption, FieldOut, SensorStatus, WaterVault } from '@/lib/types';

const RECENT_DAYS = 14;

/**
 * The farmer's view of the Water Vault: the same computation as the staff screen, shown for
 * the field's default crop and decision day. Read only; calibration and regional checks stay
 * with the staff.
 */
export async function FarmerWaterContent({ params }: { params: { field?: string } }) {
  const [t, locale, fields, crops] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
    api<CropOption[]>('/reference/crops'),
  ]);
  const number = (value: number | null, digits = 0) => formatNumber(value, locale, digits);

  const banner = (
    <header className="zira-farm-banner">
      <MeadowBanner />
      <div>
        <h1 className="zira-farm-title">{t('screens.myWater.title')}</h1>
        <p className="zira-farm-lede">{t('screens.myWater.description')}</p>
      </div>
    </header>
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack zira-farmer zira-farm">
        {banner}
        <p className="zira-farm-card">{t('farmerView.noFields')}</p>
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  const crop = crops.find((candidate) => candidate.season_type !== null) ?? crops[0];

  const tabs =
    fields.length > 1 ? (
      <nav className="zira-farm-tabs" aria-label={t('fieldMemory.form.field')}>
        {fields.map((candidate) => (
          <Link
            key={candidate.id}
            href={`/water-vault?field=${candidate.id}`}
            aria-current={candidate.id === field.id ? 'page' : undefined}
          >
            {candidate.name}
          </Link>
        ))}
      </nav>
    ) : null;

  let vault: WaterVault;
  try {
    vault = await api<WaterVault>(
      `/fields/${encodeURIComponent(field.id)}/water-vault?crop=${encodeURIComponent(crop.key)}`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && error.detail?.code) {
      const code = error.detail.code;
      const known = t.has(`waterVault.errors.${code}`) ? code : 'generic';
      const values: Record<string, string | number> = {};
      for (const key of ['last_date', 'first_date', 'earliest_date']) {
        const value = error.detail[key];
        if (typeof value === 'string') values[key] = formatDate(value, locale);
      }
      for (const key of ['missing_days', 'days']) {
        const value = error.detail[key];
        if (typeof value === 'number') values[key] = value;
      }
      return (
        <div className="zira-stack zira-farmer zira-farm">
          {banner}
          {tabs}
          <Alert tone="warning">{t(`waterVault.errors.${known}`, values)}</Alert>
        </div>
      );
    }
    throw error;
  }

  const sensorStatus = await api<SensorStatus>(`/fields/${encodeURIComponent(field.id)}/sensors`);
  const { decision, window: span } = vault;
  const cropName = t.has(`crops.${crop.key}`) ? t(`crops.${crop.key}`) : crop.name_tr;
  const percent = Math.min(100, Math.max(0, decision.fill_fraction * 100));
  const dates = vault.daily.map((day) => day.date);
  const monthYear = (iso: string) =>
    new Intl.DateTimeFormat(locale, { month: 'short', year: '2-digit', timeZone: 'UTC' }).format(
      new Date(`${iso}T00:00:00Z`),
    );
  const et0Max = Math.max(1, ...vault.daily.map((day) => day.et0_mm ?? 0));
  const tick = (value: number) => number(value, Number.isInteger(value) ? 0 : 1);
  const recent = vault.daily.slice(-RECENT_DAYS).reverse();

  return (
    <div className="zira-stack zira-farmer zira-farm">
      {banner}
      {tabs}

      <section className="zira-farm-card" aria-labelledby="water-main">
        <div className="zira-farm-water">
          <DropIllustration />
          <div>
            <h2 id="water-main" className="zira-farm-meta">
              {t('farmerView.waterTitle')}
            </h2>
            <p className="zira-farm-figure">{t('waterVault.mm', { value: number(decision.storage_mm) })}</p>
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
        <p>{t('waterVault.fill', { percent: number(decision.fill_fraction * 100) })}</p>
        <p>
          <span className="zira-farm-range">
            {t('waterVault.kpi.range')}:{' '}
            {t('waterVault.rangeValue', { low: number(decision.low_mm), high: number(decision.high_mm) })}
          </span>
        </p>
        <p className="zira-farm-meta">
          {t(vault.date_is_default ? 'waterVault.decisionDay' : 'waterVault.chosenDay', {
            date: formatDate(vault.date, locale),
          })}{' '}
          · {cropName} · {field.name}
        </p>
        <p>
          <Badge tone={vault.mode === 'sensor' ? 'success' : 'neutral'}>
            {t(`waterVault.mode.${vault.mode}`)}
          </Badge>
        </p>
      </section>

      <div className="zira-farm-facts-row">
        <section className="zira-farm-card">
          <h3>{t('waterVault.kpi.capacity')}</h3>
          <p className="zira-farm-figure zira-farm-figure--small">
            {t('waterVault.mm', { value: number(decision.taw_mm) })}
          </p>
        </section>
        <section className="zira-farm-card">
          <h3>{t('waterVault.kpi.gaps')}</h3>
          <p className="zira-farm-figure zira-farm-figure--small">{span.missing_days}</p>
        </section>
      </div>

      {vault.needs_signoff.length > 0 && (
        <Alert tone="warning" title={t('waterVault.draft.title')}>
          {t('waterVault.draft.body')}{' '}
          {vault.needs_signoff
            .map((name) => (t.has(`waterVault.params.${name}`) ? t(`waterVault.params.${name}`) : name))
            .join(', ')}
          .
        </Alert>
      )}

      {vault.sensor ? (
        <section className="zira-farm-card" aria-labelledby="sensor-title">
          <h2 id="sensor-title">{t('waterVault.sensorTitle')}</h2>
          <p>
            {t('waterVault.sensorCompare', {
              model: number(vault.sensor.model_mm),
              sensor: number(vault.sensor.sensor_mm),
              difference: number(vault.sensor.difference_mm),
            })}
          </p>
          <p className="zira-farm-meta">
            {t('waterVault.sensorWhere', {
              date: formatDateTime(vault.sensor.measured_at, locale),
              nodes: vault.sensor.nodes,
              depths: vault.sensor.depths_cm.join(', '),
            })}
          </p>
          {sensorStatus.nodes.some((node) => node.is_simulated) && (
            <Alert tone="info">{t('waterVault.simulated')}</Alert>
          )}
        </section>
      ) : (
        <Alert tone="info">{t('waterVault.satelliteHint', { hours: sensorStatus.silence_h })}</Alert>
      )}

      <section className="zira-farm-card" aria-labelledby="storage-title">
        <div className="zira-farm-fieldhead">
          <SproutIllustration />
          <h2 id="storage-title">{t('waterVault.charts.storageTitle')}</h2>
        </div>
        <LineChart
          dates={dates}
          yMax={Math.max(decision.taw_mm, ...vault.daily.map((day) => day.storage_mm))}
          ariaLabel={t('waterVault.charts.storageAria')}
          formatDate={monthYear}
          formatTick={tick}
          series={[
            {
              label: t('waterVault.charts.storageLegend'),
              values: vault.daily.map((day) => day.storage_mm),
              tone: 'primary',
            },
            {
              label: t('waterVault.charts.capacityLegend'),
              values: vault.daily.map(() => decision.taw_mm),
              tone: 'muted',
              dashed: true,
            },
          ]}
        />
        <div className="zira-legend">
          <span>
            <span className="zira-legend-swatch" />
            {t('waterVault.charts.storageLegend')}
          </span>
          <span>
            <span className="zira-legend-swatch zira-legend-swatch--muted" />
            {t('waterVault.charts.capacityLegend')}
          </span>
        </div>
      </section>

      <details className="zira-farm-card zira-farm-details">
        <summary>{t('waterVault.technical')}</summary>
        <div className="zira-stack">
          <h3>{t('waterVault.assumptionsTitle')}</h3>
          <ul className="zira-list">
            {vault.assumptions.map((code) => (
              <li key={code}>
                {t(`waterVault.assumptions.${code}`, {
                  days: vault.parameters.spinup_days,
                  delta: number(vault.parameters.uncertainty_delta, 1),
                  bandMm: number(vault.sensor?.band_mm ?? 0),
                })}
              </li>
            ))}
            <li>
              {t('waterVault.window', {
                days: span.days,
                start: formatDate(span.start, locale),
                end: formatDate(span.end, locale),
              })}
            </li>
          </ul>

          <h3>{t('waterVault.charts.et0Title')}</h3>
          {vault.et0_blocker ? (
            <Alert tone="info">{t(`waterVault.et0Blocker.${vault.et0_blocker}`)}</Alert>
          ) : (
            <LineChart
              dates={dates}
              yMax={et0Max}
              ariaLabel={t('waterVault.charts.et0Aria')}
              formatDate={monthYear}
              formatTick={tick}
              series={[
                {
                  label: t('waterVault.charts.et0Legend'),
                  values: vault.daily.map((day) => day.et0_mm),
                  tone: 'primary',
                },
              ]}
            />
          )}

          <h3>{t('waterVault.recentTitle')}</h3>
          <TableContainer label={t('waterVault.recentTitle')} appearance="card">
            <Table density="compact">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>{t('waterVault.columns.date')}</TableHeaderCell>
                  <TableHeaderCell align="end">{t('waterVault.columns.precip')}</TableHeaderCell>
                  <TableHeaderCell align="end">{t('waterVault.columns.et0')}</TableHeaderCell>
                  <TableHeaderCell align="end">{t('waterVault.columns.storage')}</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recent.map((day) => (
                  <TableRow key={day.date}>
                    <TableCell>{formatDate(day.date, locale)}</TableCell>
                    <TableCell numeric>{number(day.precipitation_mm, 1)}</TableCell>
                    <TableCell numeric>{number(day.et0_mm, 1)}</TableCell>
                    <TableCell numeric>{number(day.storage_mm, 1)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      </details>

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
