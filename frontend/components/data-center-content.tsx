import {
  Alert,
  PageHeader,
  Section,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { api } from '@/lib/api';
import { formatDate, formatDateTime } from '@/lib/format';
import { JOB_BADGE, SOURCE_BADGE } from '@/lib/status';
import type { JobOut, SourceOut } from '@/lib/types';

/** Whether NASA data really arrives: every source, and every fetch job with its outcome. */
export async function DataCenterContent() {
  const [t, locale, sources, jobs] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<SourceOut[]>('/data-center/sources'),
    api<JobOut[]>('/data-center/jobs?limit=50'),
  ]);

  return (
    <div className="zira-stack">
      <PageHeader
        title={t('screens.dataCenter.title')}
        description={t('screens.dataCenter.description')}
      />

      <Alert tone="info">{t('dataCenter.regionalNote')}</Alert>

      <Section title={t('dataCenter.sourcesTitle')}>
        <TableContainer label={t('dataCenter.sourcesTitle')} appearance="card">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>{t('dataCenter.columns.source')}</TableHeaderCell>
                <TableHeaderCell>{t('dataCenter.columns.resolution')}</TableHeaderCell>
                <TableHeaderCell>{t('dataCenter.columns.status')}</TableHeaderCell>
                <TableHeaderCell>{t('dataCenter.columns.lastSuccess')}</TableHeaderCell>
                <TableHeaderCell align="end">{t('dataCenter.columns.records')}</TableHeaderCell>
                <TableHeaderCell>{t('dataCenter.columns.jobs')}</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sources.map((source) => (
                <TableRow key={source.key}>
                  <TableCell
                    secondary={
                      t.has(`dataCenter.roles.${source.key}`)
                        ? t(`dataCenter.roles.${source.key}`)
                        : undefined
                    }
                  >
                    {source.name}
                  </TableCell>
                  <TableCell>{source.resolution}</TableCell>
                  <TableCell>
                    <StatusBadge status={SOURCE_BADGE[source.status]}>
                      {t(`status.source.${source.status}`)}
                    </StatusBadge>
                  </TableCell>
                  <TableCell>
                    {source.connected ? formatDateTime(source.last_success_at, locale) : '—'}
                  </TableCell>
                  <TableCell numeric>
                    {source.connected ? t('dataCenter.records', { count: source.observations }) : '—'}
                  </TableCell>
                  <TableCell>
                    {source.connected
                      ? t('dataCenter.jobsSummary', {
                          done: source.jobs.done,
                          failed: source.jobs.failed,
                          active: source.jobs.queued + source.jobs.running,
                        })
                      : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <p className="zira-muted">{t('dataCenter.notConnected')}</p>
      </Section>

      <Section title={t('dataCenter.jobsTitle')}>
        {jobs.length === 0 ? (
          <p>{t('dataCenter.jobsEmpty')}</p>
        ) : (
          <TableContainer label={t('dataCenter.jobsTitle')} appearance="card">
            <Table density="compact">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>{t('dataCenter.columns.started')}</TableHeaderCell>
                  <TableHeaderCell>{t('dataCenter.columns.field')}</TableHeaderCell>
                  <TableHeaderCell>{t('dataCenter.columns.period')}</TableHeaderCell>
                  <TableHeaderCell>{t('dataCenter.columns.status')}</TableHeaderCell>
                  <TableHeaderCell align="end">{t('dataCenter.columns.rows')}</TableHeaderCell>
                  <TableHeaderCell>{t('dataCenter.columns.error')}</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>{formatDateTime(job.created_at, locale)}</TableCell>
                    <TableCell secondary={job.field_code}>{job.field_name ?? '—'}</TableCell>
                    <TableCell>
                      {formatDate(job.date_from, locale)} – {formatDate(job.date_to, locale)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={JOB_BADGE[job.status]}>
                        {t(`status.job.${job.status}`)}
                      </StatusBadge>
                    </TableCell>
                    <TableCell numeric>
                      {job.rows_written === null
                        ? '—'
                        : job.rows_written === 0 && job.status === 'done'
                          ? t('dataCenter.cached')
                          : job.rows_written}
                    </TableCell>
                    <TableCell>{job.error_message ?? '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Section>

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
