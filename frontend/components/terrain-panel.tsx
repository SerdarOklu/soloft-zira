'use client';

import { Alert, Button, DescriptionList, Section, Spinner } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';

import { useRouter } from '@/i18n/navigation';
import { formatNumber } from '@/lib/format';
import { isActive } from '@/lib/status';
import type { JobOut } from '@/lib/types';

export interface Terrain {
  available: boolean;
  elevation_m: number | null;
  elevation_min_m: number | null;
  elevation_max_m: number | null;
  slope_deg: number | null;
  latest_job: JobOut | null;
}

const POLL_MS = 2000;
const MAX_POLLS = 90;
type Notice = { tone: 'danger' | 'success' | 'warning'; text: string };
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** The field's elevation and slope from SRTM (NASADEM), read for the polygon on request. */
export function TerrainPanel({ fieldId, initial }: { fieldId: string; initial: Terrain }) {
  const t = useTranslations('terrain');
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
  const base = `/api/backend/fields/${fieldId}/terrain`;
  const number = (value: number | null, digits = 0) => formatNumber(value, locale, digits);

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
        setNotice({ tone: 'danger', text: t(response.status === 409 ? 'errors.running' : 'errors.generic') });
        return;
      }
      const job = (await response.json()) as JobOut;
      let current = job;
      for (let poll = 0; poll < MAX_POLLS && isActive(current.status) && mounted.current; poll++) {
        await sleep(POLL_MS);
        const next = await fetch(base, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null));
        if (next?.latest_job?.id === job.id) current = next.latest_job as JobOut;
      }
      if (!mounted.current) return;
      if (current.status === 'done') {
        setNotice({ tone: 'success', text: t('done') });
        router.refresh();
      } else if (current.status === 'failed') {
        setNotice({ tone: 'danger', text: `${t('failed')}: ${current.error_message ?? ''}`.trim() });
      } else {
        setNotice({ tone: 'warning', text: t('errors.slow') });
      }
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
        <Button onClick={start} loading={busy} variant={initial.available ? 'secondary' : 'primary'}>
          {initial.available ? t('refetch') : t('fetch')}
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
        {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
        {initial.available ? (
          <DescriptionList
            variant="compact"
            items={[
              [t('elevation'), t('meters', { value: number(initial.elevation_m) })],
              [
                t('range'),
                t('rangeValue', {
                  low: number(initial.elevation_min_m),
                  high: number(initial.elevation_max_m),
                }),
              ],
              [t('slope'), t('degrees', { value: number(initial.slope_deg, 1) })],
            ]}
          />
        ) : (
          !busy && <p>{t('none')}</p>
        )}
        <p className="zira-muted">{t('limits')}</p>
      </div>
    </Section>
  );
}
