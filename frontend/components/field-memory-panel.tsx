'use client';

import {
  Alert,
  Badge,
  Button,
  Section,
  Select,
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

import { LineChart } from '@/components/line-chart';
import { useRouter } from '@/i18n/navigation';
import { formatDate, formatNumber } from '@/lib/format';
import { isActive } from '@/lib/status';
import type { CycleState, FieldMemory, JobOut } from '@/lib/types';

const POLL_MS = 3000;
// About ten minutes: ten years of composites normally take a few minutes.
const MAX_POLLS = 200;
const STATES: CycleState[] = ['cropped', 'fallow', 'unknown'];
const STATE_TONE = { cropped: 'success', fallow: 'neutral', unknown: 'warning' } as const;
const LEVEL_TONE = { high: 'success', medium: 'warning', low: 'danger' } as const;

type Notice = { tone: 'danger' | 'warning' | 'success'; text: string };

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** The NDVI series, the cropped or fallow history it implies, and the person's confirmation. */
export function FieldMemoryPanel({ fieldId, memory }: { fieldId: string; memory: FieldMemory }) {
  const t = useTranslations('fieldMemory');
  const locale = useLocale();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [choices, setChoices] = useState<Record<string, CycleState>>({});
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const base = `/api/backend/fields/${fieldId}/field-memory`;
  const number = (value: number | null, digits = 2) => formatNumber(value, locale, digits);
  const hasData = memory.coverage.observations > 0;
  const unknownCount = memory.seasons.filter((s) => s.detected_state === 'unknown').length;
  const choice = (season: FieldMemory['seasons'][number]): CycleState =>
    choices[season.season] ?? season.confirmed_state ?? season.detected_state;

  async function latestJobs(): Promise<JobOut[] | null> {
    try {
      const response = await fetch(base, { cache: 'no-store' });
      return response.ok ? ((await response.json()) as FieldMemory).latest_jobs : null;
    } catch {
      return null;
    }
  }

  async function start() {
    setBusy(true);
    setNotice(null);
    try {
      const response = await fetch(`${base}/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      if (!response.ok) {
        const json = (await response.json().catch(() => null)) as { detail?: { code?: string } } | null;
        const code = json?.detail?.code;
        setNotice({
          tone: 'danger',
          text: t(code && t.has(`errors.${code}`) ? `errors.${code}` : 'errors.generic'),
        });
        return;
      }
      const queued = (await response.json()) as JobOut[];
      const ids = new Set(queued.map((job) => job.id));
      let current: JobOut[] = queued;
      for (
        let poll = 0;
        poll < MAX_POLLS && current.some((job) => isActive(job.status)) && mounted.current;
        poll++
      ) {
        await sleep(POLL_MS);
        const next = await latestJobs();
        if (next) current = next.filter((job) => ids.has(job.id));
      }
      if (!mounted.current) return;
      const failed = current.find((job) => job.status === 'failed');
      if (failed) {
        setNotice({ tone: 'danger', text: `${t('fetchFailed')}: ${failed.error_message ?? ''}`.trim() });
      } else if (current.every((job) => job.status === 'done')) {
        setNotice({ tone: 'success', text: t('fetchDone') });
      } else {
        setNotice({ tone: 'warning', text: t('errors.slow') });
      }
      router.refresh();
    } catch {
      setNotice({ tone: 'danger', text: t('errors.generic') });
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  async function confirm() {
    setBusy(true);
    setNotice(null);
    try {
      const response = await fetch(`${base}/confirm?source=${memory.source}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          seasons: memory.seasons.map((season) => ({ season: season.season, state: choice(season) })),
        }),
      });
      if (!response.ok) {
        setNotice({ tone: 'danger', text: t('errors.generic') });
        return;
      }
      setChoices({});
      setNotice({ tone: 'success', text: t('saved') });
      router.refresh();
    } catch {
      setNotice({ tone: 'danger', text: t('errors.generic') });
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  const dates = memory.series.map((point) => point.date);
  const monthYear = (iso: string) =>
    new Intl.DateTimeFormat(locale, { month: 'short', year: '2-digit', timeZone: 'UTC' }).format(
      new Date(`${iso}T00:00:00Z`),
    );

  return (
    <div className="zira-stack">
      <Section
        title={t('chart.title')}
        actions={
          <Button onClick={start} loading={busy} variant={hasData ? 'secondary' : 'primary'}>
            {hasData ? t('refetch') : t('fetch')}
          </Button>
        }
      >
        <div className="zira-stack">
          {busy && (
            <p className="zira-actions" role="status">
              <Spinner size="sm" /> {t('fetching')}
            </p>
          )}
          {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
          {!hasData ? (
            !busy && <p>{t('none')}</p>
          ) : (
            <>
              <p className="zira-muted">
                {t('usedSource', {
                  source: t(`sources.${memory.source}`),
                  landsat: memory.available_sources.landsat ?? 0,
                  modis: memory.available_sources.modis ?? 0,
                })}
              </p>
              <p className="zira-muted">
                {t('coverage', {
                  count: memory.coverage.observations,
                  good: memory.coverage.good,
                  from: formatDate(memory.coverage.first_date, locale),
                  to: formatDate(memory.coverage.last_date, locale),
                })}
              </p>
              <LineChart
                dates={dates}
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
            </>
          )}
          <p className="zira-muted">{t('source')}</p>
        </div>
      </Section>

      {hasData && (
        <>
          {memory.provisional && (
            <Alert tone="warning" title={t('provisional.title')}>
              {t('provisional.body', { value: number(memory.threshold) })}
            </Alert>
          )}
          {unknownCount > 0 && <Alert tone="info">{t('unknownWarning', { count: unknownCount })}</Alert>}

          <Section title={t('seasons.title')}>
            <TableContainer label={t('seasons.title')} appearance="card">
              <Table density="compact">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>{t('columns.season')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.detected')}</TableHeaderCell>
                    <TableHeaderCell align="end">{t('columns.peak')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.confidence')}</TableHeaderCell>
                    <TableHeaderCell align="end">{t('columns.images')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.confirm')}</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {memory.seasons.map((season) => (
                    <TableRow key={season.season}>
                      <TableCell>{season.season}</TableCell>
                      <TableCell>
                        <Badge tone={STATE_TONE[season.detected_state]}>
                          {t(`states.${season.detected_state}`)}
                        </Badge>
                      </TableCell>
                      <TableCell numeric>
                        {season.peak_ndvi === null
                          ? '—'
                          : `${number(season.peak_ndvi)} · ${formatDate(season.peak_date, locale)}`}
                      </TableCell>
                      <TableCell>
                        {season.confidence_level ? (
                          <Badge tone={LEVEL_TONE[season.confidence_level]}>
                            {t(`levels.${season.confidence_level}`)}
                          </Badge>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell numeric>
                        {season.good_observations} / {season.total_observations}
                      </TableCell>
                      <TableCell>
                        <Select
                          aria-label={`${t('columns.confirm')} ${season.season}`}
                          value={choice(season)}
                          onChange={(event) =>
                            setChoices((current) => ({
                              ...current,
                              [season.season]: event.target.value as CycleState,
                            }))
                          }
                        >
                          {STATES.map((state) => (
                            <option key={state} value={state}>
                              {t(`states.${state}`)}
                            </option>
                          ))}
                        </Select>
                        {season.confirmed_by && (
                          <span className="zira-muted"> {t(`confirmed.by.${season.confirmed_by}`)}</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <div className="zira-actions">
              <Button onClick={confirm} loading={busy}>
                {t('confirm')}
              </Button>
              <span className="zira-muted">
                {t('confirmed.summary', {
                  count: memory.confirmed_count,
                  total: memory.seasons.length,
                })}
              </span>
              {memory.confirmed_count >= 2 && (
                <Button
                  variant="secondary"
                  href={`/rotation?${new URLSearchParams({ field: fieldId, rotation: 'history' })}`}
                >
                  {t('useAsA')}
                </Button>
              )}
            </div>
          </Section>
        </>
      )}

      <p className="zira-muted">{t('limits')}</p>
    </div>
  );
}
