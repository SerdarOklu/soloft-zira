'use client';

import { Alert, Button, Section, Spinner } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';

import { LineChart } from '@/components/line-chart';
import { useRouter } from '@/i18n/navigation';
import { formatDate, formatNumber } from '@/lib/format';
import { isActive } from '@/lib/status';
import type { JobOut } from '@/lib/types';

export interface Regional {
  configured: boolean;
  smap: {
    days: number;
    mean_am: number | null;
    mean_pm: number | null;
    last_date: string | null;
    series: { date: string; am: number | null; pm: number | null }[];
  };
  gpm: {
    days: number;
    imerg_total_mm: number | null;
    power_total_mm: number | null;
    correlation: number | null;
    series: { date: string; imerg_mm: number; power_mm: number | null }[];
  };
  grace: {
    months: number;
    first_date: string | null;
    last_date: string | null;
    latest_cm: number | null;
    trend_cm_per_year: number | null;
  };
  latest_jobs: JobOut[];
}

const POLL_MS = 4000;
// About 25 minutes: SMAP reads one large file per day.
const MAX_POLLS = 375;
type Notice = { tone: 'danger' | 'success' | 'warning'; text: string };
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** SMAP, GPM IMERG and GRACE next to the model: regional checks, never inputs and never a field measurement. */
export function RegionalPanel({
  fieldId,
  regional,
  canFetch,
}: {
  fieldId: string;
  regional: Regional;
  canFetch: boolean;
}) {
  const t = useTranslations('regional');
  const locale = useLocale();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const base = `/api/backend/fields/${fieldId}/regional`;
  const number = (value: number | null, digits = 1) => formatNumber(value, locale, digits);
  const monthYear = (iso: string) =>
    new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(
      new Date(`${iso}T00:00:00Z`),
    );
  const { smap, gpm, grace } = regional;
  const hasAny = smap.days > 0 || gpm.days > 0 || grace.months > 0;

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
        const next = await fetch(base, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null));
        if (next) current = (next as Regional).latest_jobs.filter((job) => ids.has(job.id));
      }
      if (!mounted.current) return;
      const failed = current.find((job) => job.status === 'failed');
      if (failed) {
        setNotice({
          tone: 'danger',
          text: `${t('failed', { source: failed.source.toUpperCase() })}: ${failed.error_message ?? ''}`.trim(),
        });
      } else if (current.every((job) => job.status === 'done')) {
        setNotice({ tone: 'success', text: t('done') });
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

  return (
    <Section
      title={t('title')}
      actions={
        canFetch && regional.configured ? (
          <Button onClick={start} loading={busy} variant={hasAny ? 'secondary' : 'primary'}>
            {hasAny ? t('refetch') : t('fetch')}
          </Button>
        ) : undefined
      }
    >
      <div className="zira-stack">
        <p className="zira-muted">{t('description')}</p>
        {!regional.configured && <Alert tone="info">{t('notConfigured')}</Alert>}
        {busy && (
          <p className="zira-actions" role="status">
            <Spinner size="sm" /> {t('fetching')}
          </p>
        )}
        {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
        {!hasAny && regional.configured && !busy && <p>{t('none')}</p>}

        {smap.days > 0 && (
          <div className="zira-stack">
            <h3 className="zira-subheading">{t('smap.title')}</h3>
            <p>
              {t('smap.summary', {
                days: smap.days,
                am: number(smap.mean_am, 3),
                pm: number(smap.mean_pm, 3),
              })}
            </p>
            <LineChart
              dates={smap.series.map((point) => point.date)}
              yMax={0.4}
              ariaLabel={t('smap.aria')}
              formatDate={monthYear}
              formatTick={(value) => number(value, 2)}
              series={[
                { label: t('smap.am'), values: smap.series.map((p) => p.am), tone: 'primary' },
                { label: t('smap.pm'), values: smap.series.map((p) => p.pm), tone: 'muted', dashed: true },
              ]}
            />
            <p className="zira-muted">{t('smap.limits')}</p>
          </div>
        )}

        {gpm.days > 0 && (
          <div className="zira-stack">
            <h3 className="zira-subheading">{t('gpm.title')}</h3>
            <p>
              {t('gpm.summary', {
                days: gpm.days,
                power: number(gpm.power_total_mm, 0),
                imerg: number(gpm.imerg_total_mm, 0),
              })}{' '}
              {gpm.correlation !== null && t('gpm.correlation', { r: number(gpm.correlation, 2) })}
            </p>
            <LineChart
              dates={gpm.series.map((point) => point.date)}
              yMax={Math.max(5, ...gpm.series.flatMap((p) => [p.imerg_mm, p.power_mm ?? 0]))}
              ariaLabel={t('gpm.aria')}
              formatDate={monthYear}
              formatTick={(value) => number(value, 0)}
              series={[
                { label: t('gpm.power'), values: gpm.series.map((p) => p.power_mm), tone: 'primary' },
                { label: t('gpm.imerg'), values: gpm.series.map((p) => p.imerg_mm), tone: 'muted', dashed: true },
              ]}
            />
            <p className="zira-muted">{t('gpm.limits')}</p>
          </div>
        )}

        {grace.months > 0 && (
          <div className="zira-stack">
            <h3 className="zira-subheading">{t('grace.title')}</h3>
            <p>
              {grace.trend_cm_per_year !== null
                ? t('grace.trend', {
                    value: number(grace.trend_cm_per_year, 2),
                    from: formatDate(grace.first_date, locale),
                    to: formatDate(grace.last_date, locale),
                  })
                : t('grace.noTrend')}{' '}
              {t('grace.latest', { value: number(grace.latest_cm, 1) })}
            </p>
            <p className="zira-muted">{t('grace.limits')}</p>
          </div>
        )}
      </div>
    </Section>
  );
}
