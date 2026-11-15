import {
  Alert,
  Badge,
  Button,
  EmptyState,
  KpiCard,
  KpiGrid,
  PageHeader,
  Section,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { Droplets, Gauge, Layers, TriangleAlert } from 'lucide-react';
import { getLocale, getTranslations } from 'next-intl/server';

import { LineChart } from '@/components/line-chart';
import { SensorPanel } from '@/components/sensor-panel';
import { WaterVaultForm } from '@/components/water-vault-form';
import { ApiError, api } from '@/lib/api';
import { formatDate, formatDateTime, formatNumber } from '@/lib/format';
import { getSessionUser } from '@/lib/session';
import type { CropOption, FieldOut, SensorStatus, WaterVault } from '@/lib/types';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const RECENT_DAYS = 14;

export interface WaterVaultParams {
  field?: string;
  crop?: string;
  date?: string;
}

/** The usable water on a decision day, with its range and what it rests on. */
export async function WaterVaultContent({ params }: { params: WaterVaultParams }) {
  const [t, locale, fields, crops] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
    api<CropOption[]>('/reference/crops'),
  ]);

  const header = (
    <PageHeader
      title={t('screens.waterVault.title')}
      description={t('screens.waterVault.description')}
    />
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack">
        {header}
        <EmptyState
          appearance="framed"
          title={t('waterVault.noFieldsTitle')}
          description={t('waterVault.noFieldsDescription')}
          locale={locale === 'en' ? 'en' : 'tr'}
          actions={<Button href="/fields/new">{t('waterVault.addField')}</Button>}
        />
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  // The first crop whose sowing season is known; the user can choose any other.
  const crop =
    crops.find((candidate) => candidate.key === params.crop) ??
    crops.find((candidate) => candidate.season_type !== null) ??
    crops[0];
  const date = params.date && ISO_DATE.test(params.date) ? params.date : '';

  let vault: WaterVault | null = null;
  let problem: { code: string; detail: Record<string, unknown> } | null = null;
  try {
    vault = await api<WaterVault>(
      `/fields/${encodeURIComponent(field.id)}/water-vault?crop=${encodeURIComponent(crop.key)}${date ? `&date=${date}` : ''}`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && error.detail?.code) {
      problem = { code: error.detail.code, detail: error.detail };
    } else {
      throw error;
    }
  }

  const cropName = t.has(`crops.${crop.key}`) ? t(`crops.${crop.key}`) : crop.name_tr;
  const form = (
    <WaterVaultForm
      fields={fields.map(({ id, name, code }) => ({ id, name, code }))}
      crops={crops.map(({ key, name_tr }) => ({ key, name_tr }))}
      field={field.id}
      crop={crop.key}
      date={date}
    />
  );

  if (problem) {
    const known = t.has(`waterVault.errors.${problem.code}`) ? problem.code : 'generic';
    const detail = problem.detail;
    const values: Record<string, string | number> = {};
    for (const key of ['last_date', 'first_date', 'earliest_date']) {
      if (typeof detail[key] === 'string') values[key] = formatDate(detail[key] as string, locale);
    }
    for (const key of ['missing_days', 'days']) {
      if (typeof detail[key] === 'number') values[key] = detail[key] as number;
    }
    return (
      <div className="zira-stack">
        {header}
        {form}
        <Alert tone="warning">{t(`waterVault.errors.${known}`, values)}</Alert>
        {problem.code === 'no_weather_data' && (
          <div>
            <Button href={`/fields/${field.id}`}>{t('waterVault.goToField')}</Button>
          </div>
        )}
      </div>
    );
  }

  if (!vault) return null;

  const number = (value: number | null, digits = 0) => formatNumber(value, locale, digits);
  const { decision, window: span } = vault;
  const [sensorStatus, user] = await Promise.all([
    api<SensorStatus>(`/fields/${encodeURIComponent(field.id)}/sensors`),
    getSessionUser(),
  ]);
  const canCalibrate = user?.role === 'admin' || user?.role === 'agronomist';

  const dates = vault.daily.map((day) => day.date);
  const monthYear = (iso: string) =>
    new Intl.DateTimeFormat(locale, { month: 'short', year: '2-digit', timeZone: 'UTC' }).format(
      new Date(`${iso}T00:00:00Z`),
    );
  const et0Max = Math.max(1, ...vault.daily.map((day) => day.et0_mm ?? 0));
  const tick = (value: number) => number(value, Number.isInteger(value) ? 0 : 1);
  const recent = vault.daily.slice(-RECENT_DAYS).reverse();

  return (
    <div className="zira-stack">
      {header}
      {form}

      <p className="zira-muted">
        {t(vault.date_is_default ? 'waterVault.decisionDay' : 'waterVault.chosenDay', {
          date: formatDate(vault.date, locale),
        })}{' '}
        · {cropName} · {field.name}{' '}
        <Badge tone={vault.mode === 'sensor' ? 'success' : 'neutral'}>
          {t(`waterVault.mode.${vault.mode}`)}
        </Badge>
      </p>

      <KpiGrid overlapHero={false}>
        <KpiCard
          value={t('waterVault.mm', { value: number(decision.storage_mm) })}
          label={`${t('waterVault.kpi.usable')} · ${t('waterVault.fill', {
            percent: number(decision.fill_fraction * 100),
          })}`}
          icon={<Droplets />}
          tone="blue"
        />
        <KpiCard
          value={t('waterVault.rangeValue', {
            low: number(decision.low_mm),
            high: number(decision.high_mm),
          })}
          label={t('waterVault.kpi.range')}
          icon={<Gauge />}
          tone="cyan"
        />
        <KpiCard
          value={t('waterVault.mm', { value: number(decision.taw_mm) })}
          label={t('waterVault.kpi.capacity')}
          icon={<Layers />}
          tone="green"
        />
        <KpiCard
          value={span.missing_days}
          label={t('waterVault.kpi.gaps')}
          icon={<TriangleAlert />}
          tone={span.missing_days > 0 ? 'orange' : 'muted'}
        />
      </KpiGrid>

      {vault.sensor ? (
        <Section title={t('waterVault.sensorTitle')}>
          <div className="zira-stack">
            <p>
              {t('waterVault.sensorCompare', {
                model: number(vault.sensor.model_mm),
                sensor: number(vault.sensor.sensor_mm),
                difference: number(vault.sensor.difference_mm),
              })}
            </p>
            <p className="zira-muted">
              {t('waterVault.sensorWhere', {
                date: formatDateTime(vault.sensor.measured_at, locale),
                nodes: vault.sensor.nodes,
                depths: vault.sensor.depths_cm.join(', '),
              })}
            </p>
            {sensorStatus.nodes.some((node) => node.is_simulated) && (
              <Alert tone="info">{t('waterVault.simulated')}</Alert>
            )}
          </div>
        </Section>
      ) : (
        <Alert tone="info">{t('waterVault.satelliteHint', { hours: sensorStatus.silence_h })}</Alert>
      )}

      {vault.needs_signoff.length > 0 && (
        <Alert tone="warning" title={t('waterVault.draft.title')}>
          {t('waterVault.draft.body')}{' '}
          {vault.needs_signoff
            .map((name) => (t.has(`waterVault.params.${name}`) ? t(`waterVault.params.${name}`) : name))
            .join(', ')}
          .
        </Alert>
      )}

      <Section title={t('waterVault.assumptionsTitle')}>
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
      </Section>

      <Section title={t('waterVault.charts.storageTitle')}>
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
      </Section>

      <Section title={t('waterVault.charts.et0Title')}>
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
      </Section>

      <Section title={t('waterVault.recentTitle')}>
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
      </Section>

      {!vault.crop.season_ready && (
        <Section title={t('waterVault.season.title')}>
          <Alert tone="info">{t('waterVault.season.blocked', { crop: cropName })}</Alert>
        </Section>
      )}

      <SensorPanel fieldId={field.id} status={sensorStatus} canCalibrate={canCalibrate} />

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
