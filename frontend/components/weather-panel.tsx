'use client';

import {
  Alert,
  Badge,
  Button,
  DescriptionList,
  Section,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';

import { PrecipitationChart } from '@/components/precipitation-chart';
import { useRouter } from '@/i18n/navigation';
import { formatDate, formatDateTime, formatNumber } from '@/lib/format';
import { isActive } from '@/lib/status';
import type { JobOut, WeatherSummary } from '@/lib/types';

const POLL_MS = 2000;
// About five minutes: a 25-year fetch normally takes seconds.
const MAX_POLLS = 150;

type Message = { tone: 'danger' | 'warning' | 'success'; text: string };

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function WeatherPanel({ fieldId, initial }: { fieldId: string; initial: WeatherSummary }) {
  const t = useTranslations('weather');
  const locale = useLocale();
  const router = useRouter();
  const [summary, setSummary] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const base = `/api/backend/fields/${fieldId}/weather`;

  async function loadSummary(): Promise<WeatherSummary | null> {
    try {
      const response = await fetch(`${base}/summary`, { cache: 'no-store' });
      return response.ok ? ((await response.json()) as WeatherSummary) : null;
    } catch {
      return null;
    }
  }

  async function start() {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`${base}/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      if (!response.ok) {
        setMessage({ tone: 'danger', text: t(response.status === 503 ? 'errors.queue' : 'errors.generic') });
        return;
      }
      const job = (await response.json()) as JobOut;
      let current: JobOut = job;
      for (let poll = 0; poll < MAX_POLLS && isActive(current.status) && mounted.current; poll++) {
        await sleep(POLL_MS);
        const next = await loadSummary();
        if (next?.latest_job?.id === job.id) {
          current = next.latest_job;
          setSummary(next);
        }
      }
      if (!mounted.current) return;
      if (current.status === 'done') {
        const latest = await loadSummary();
        if (latest) setSummary(latest);
        setMessage({ tone: 'success', text: t('fetchDone') });
        router.refresh(); // the field's elevation and data count come from the server
      } else if (current.status === 'failed') {
        setMessage({
          tone: 'danger',
          text: `${t('fetchFailed')}: ${current.error_message ?? ''}`.trim(),
        });
      } else {
        setMessage({ tone: 'warning', text: t('errors.slow') });
      }
    } catch {
      setMessage({ tone: 'danger', text: t('errors.generic') });
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  const number = (value: number | null, digits = 1) => formatNumber(value, locale, digits);
  const hasData = summary.days > 0;

  return (
    <Section
      title={t('title')}
      actions={
        <Button onClick={start} loading={busy} variant={hasData ? 'secondary' : 'primary'}>
          {hasData ? t('refetch') : t('fetch')}
        </Button>
      }
    >
      <div className="zira-stack">
        <p className="zira-muted">{t('description')}</p>

        {busy && (
          <p className="zira-actions" role="status">
            <Spinner size="sm" /> {t('fetching')}
          </p>
        )}
        {message && <Alert tone={message.tone}>{message.text}</Alert>}

        {!hasData ? (
          !busy && <p>{t('none')}</p>
        ) : (
          <>
            <DescriptionList
              variant="compact"
              items={[
                [
                  t('stored'),
                  t('coverage', {
                    days: summary.days,
                    from: formatDate(summary.first_date, locale),
                    to: formatDate(summary.last_date, locale),
                  }),
                ],
                [t('lastFetched'), formatDateTime(summary.last_fetched_at, locale)],
              ]}
            />

            <div>
              <h3 className="zira-subheading">{t('chartTitle')}</h3>
              <PrecipitationChart
                years={summary.years}
                ariaLabel={t('chartAria')}
                format={(value) => number(value, 0)}
              />
              {summary.wind_height_m !== null && (
                <p className="zira-muted">
                  {t('windNote', { height: number(summary.wind_height_m, 0) })}
                </p>
              )}
            </div>

            <div>
              <h3 className="zira-subheading">{t('yearsTitle')}</h3>
              <TableContainer label={t('yearsTitle')} appearance="card">
                <Table density="compact">
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>{t('columns.year')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.days')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.precip')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.tavg')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.tmin')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.tmax')}</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.years.map((year) => (
                      <TableRow key={year.year}>
                        <TableCell>{year.year}</TableCell>
                        <TableCell numeric>{year.days}</TableCell>
                        <TableCell numeric>{number(year.precipitation_mm)}</TableCell>
                        <TableCell numeric>{number(year.temperature_avg)}</TableCell>
                        <TableCell numeric>{number(year.temperature_min)}</TableCell>
                        <TableCell numeric>{number(year.temperature_max)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </div>

            <div>
              <h3 className="zira-subheading">{t('recentTitle')}</h3>
              <TableContainer label={t('recentTitle')} appearance="card">
                <Table density="compact">
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>{t('columns.date')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.precip')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.tavg')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.humidity')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.wind')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.solar')}</TableHeaderCell>
                      <TableHeaderCell align="end">{t('columns.pressure')}</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.recent.map((day) => (
                      <TableRow key={day.date}>
                        <TableCell>
                          {formatDate(day.date, locale)}{' '}
                          {day.quality_flag && <Badge tone="warning">{t('partialDay')}</Badge>}
                        </TableCell>
                        <TableCell numeric>{number(day.precipitation_mm)}</TableCell>
                        <TableCell numeric>{number(day.temperature_avg)}</TableCell>
                        <TableCell numeric>{number(day.humidity, 0)}</TableCell>
                        <TableCell numeric>{number(day.wind_speed)}</TableCell>
                        <TableCell numeric>{number(day.solar_radiation)}</TableCell>
                        <TableCell numeric>{number(day.surface_pressure)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </div>
          </>
        )}
      </div>
    </Section>
  );
}
