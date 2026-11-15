import { Button, EmptyState, KpiCard, KpiGrid, PageHeader, Panel, PanelBody } from '@soloft/uds';
import { Activity, Database, Sprout, TriangleAlert } from 'lucide-react';
import { getLocale, getTranslations } from 'next-intl/server';

import { DashboardMap } from '@/components/dashboard-map';
import { Link } from '@/i18n/navigation';
import { api } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { DashboardSummary } from '@/lib/types';

/** The state of the system in ten seconds; no analysis happens here. */
export async function DashboardContent() {
  const [t, locale, summary] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<DashboardSummary>('/dashboard/summary'),
  ]);
  const active = summary.jobs.queued + summary.jobs.running;

  return (
    <div className="zira-stack">
      <PageHeader
        title={t('screens.dashboard.title')}
        description={t('screens.dashboard.description')}
        actions={<Button href="/fields/new">{t('dashboard.addField')}</Button>}
      />

      <KpiGrid overlapHero={false}>
        <KpiCard
          value={summary.field_count}
          label={t('dashboard.kpiFields')}
          icon={<Sprout />}
          tone="green"
          href="/fields"
        />
        <KpiCard
          value={summary.fields_with_weather}
          label={t('dashboard.kpiWithData')}
          icon={<Database />}
          tone="blue"
        />
        <KpiCard
          value={active}
          label={t('dashboard.kpiActiveJobs')}
          icon={<Activity />}
          tone="cyan"
        />
        <KpiCard
          value={summary.jobs.failed}
          label={t('dashboard.kpiFailedJobs')}
          icon={<TriangleAlert />}
          tone={summary.jobs.failed > 0 ? 'red' : 'muted'}
        />
      </KpiGrid>

      <div className="zira-grid-2">
        <Panel title={t('dashboard.mapTitle')}>
          {summary.markers.length === 0 ? (
            <EmptyState
              appearance="plain"
              level={3}
              title={t('dashboard.mapEmpty')}
              description={t('dashboard.noFields')}
              locale={locale === 'en' ? 'en' : 'tr'}
              actions={<Button href="/fields/new">{t('dashboard.addField')}</Button>}
            />
          ) : (
            <>
              <DashboardMap
                ariaLabel={t('dashboard.mapAria')}
                markers={summary.markers.map((marker) => ({
                  id: marker.id,
                  name: marker.name,
                  lat: marker.lat,
                  lon: marker.lon,
                  filled: marker.has_weather,
                }))}
              />
              <p className="zira-muted">{t('dashboard.mapLegend')}</p>
            </>
          )}
        </Panel>

        <div className="zira-stack">
          <Panel title={t('dashboard.updateTitle')}>
            <PanelBody>
              <p>
                {summary.last_weather_update
                  ? formatDateTime(summary.last_weather_update, locale)
                  : t('dashboard.updateNever')}
              </p>
            </PanelBody>
          </Panel>

          <Panel title={t('dashboard.missingTitle')}>
            <PanelBody
              empty={summary.field_count === 0 ? t('dashboard.noFields') : t('dashboard.missingEmpty')}
            >
              {summary.fields_missing_weather.length > 0 && (
                <ul className="zira-list">
                  {summary.fields_missing_weather.map((field) => (
                    <li key={field.id}>
                      <Link href={`/fields/${field.id}`}>{field.name}</Link>{' '}
                      <span className="zira-muted">{field.code}</span>
                    </li>
                  ))}
                </ul>
              )}
            </PanelBody>
          </Panel>
        </div>
      </div>

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
