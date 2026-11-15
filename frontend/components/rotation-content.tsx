import { Alert, Badge, Button, EmptyState, PageHeader, Section } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { PrintButton } from '@/components/print-button';
import { RotationForm } from '@/components/rotation-form';
import { ApiError, api } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/format';
import { ROTATION_PRESETS } from '@/lib/rotation';
import type { FieldOut, RotationComparison, RotationSeason, RotationStrategy } from '@/lib/types';

export interface RotationParams {
  field?: string;
  rotation?: string;
}

const KNOWN_ROTATIONS = new Set<string>(Object.values(ROTATION_PRESETS));
const TEXT_ROWS = ['rationale', 'evidence', 'benefit', 'gap', 'risk'] as const;

function seasonState(season: RotationSeason): 'sufficient' | 'short' | 'fallow' | 'heldBack' | 'invalid' {
  if (season.crop === null) return season.planned === null ? 'fallow' : 'heldBack';
  if (!season.valid) return 'invalid';
  return season.sufficient ? 'sufficient' : 'short';
}

/** Zira Card: strategies A, B and C on one field, with what each one rests on. */
export async function RotationContent({ params }: { params: RotationParams }) {
  const [t, locale, fields] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);

  const header = (
    <PageHeader title={t('screens.rotation.title')} description={t('screens.rotation.description')} />
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack">
        {header}
        <EmptyState
          appearance="framed"
          title={t('rotation.noFieldsTitle')}
          description={t('rotation.noFieldsDescription')}
          locale={locale === 'en' ? 'en' : 'tr'}
          actions={<Button href="/fields/new">{t('rotation.addField')}</Button>}
        />
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  const rotation =
    params.rotation && KNOWN_ROTATIONS.has(params.rotation)
      ? params.rotation
      : ROTATION_PRESETS.wheatFallow;
  const form = (
    <RotationForm
      fields={fields.map(({ id, name, code }) => ({ id, name, code }))}
      field={field.id}
      rotation={rotation}
    />
  );

  let card: RotationComparison | null = null;
  let problem: string | null = null;
  try {
    card = await api<RotationComparison>(
      `/fields/${encodeURIComponent(field.id)}/rotation?rotation=${encodeURIComponent(rotation)}`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && error.detail?.code) {
      problem = error.detail.code;
    } else {
      throw error;
    }
  }

  if (problem) {
    const known = t.has(`rotation.errors.${problem}`) ? problem : 'generic';
    return (
      <div className="zira-stack">
        {header}
        {form}
        <Alert tone="warning">{t(`rotation.errors.${known}`)}</Alert>
        {problem === 'no_weather_data' && (
          <div>
            <Button href={`/fields/${field.id}`}>{t('rotation.goToField')}</Button>
          </div>
        )}
      </div>
    );
  }
  if (!card) return null;

  const number = (value: number | null, digits = 0) => formatNumber(value, locale, digits);
  const signed = (value: number | null, digits = 1) =>
    value === null ? '—' : `${value > 0 ? '+' : ''}${number(value, digits)}`;
  const cropLabel = (key: string) => (t.has(`crops.${key}`) ? t(`crops.${key}`) : key);

  return (
    <div className="zira-stack zira-card-page">
      {header}
      <div className="zira-no-print">{form}</div>

      <p className="zira-muted">
        {t('rotation.summary', {
          field: field.name,
          count: card.seasons,
          first: formatDate(card.first_day, locale),
          last: formatDate(card.last_day, locale),
        })}
      </p>

      {card.provisional && (
        <Alert tone="warning" title={t('rotation.provisional.title')}>
          {t('rotation.provisional.body')}{' '}
          {card.provisional_sources.map((code) => t(`rotation.provisionalSources.${code}`)).join(', ')}
          .
        </Alert>
      )}

      <div className="zira-strategies">
        {card.strategies.map((strategy) => (
          <StrategyBlock
            key={strategy.key}
            strategy={strategy}
            t={t}
            number={number}
            signed={signed}
            cropLabel={cropLabel}
          />
        ))}
      </div>

      <Section title={t('rotation.seasons.title')}>
        <ul className="zira-legend zira-season-legend">
          {(['sufficient', 'short', 'fallow', 'heldBack', 'invalid'] as const).map((state) => (
            <li key={state}>
              <span className={`zira-season zira-season--${state}`} />
              {t(`rotation.seasons.${state}`)}
            </li>
          ))}
        </ul>
      </Section>

      <Section title={t('rotation.assumptionsTitle')}>
        <ul className="zira-list">
          {card.assumptions.map((code) => (
            <li key={code}>{t(`rotation.assumptions.${code}`)}</li>
          ))}
        </ul>
        {card.needs_signoff.length > 0 && (
          <p className="zira-muted">
            {t('rotation.needsSignoff')}{' '}
            {card.needs_signoff
              .map((name) => (t.has(`waterVault.params.${name}`) ? t(`waterVault.params.${name}`) : name))
              .join(', ')}
            .
          </p>
        )}
      </Section>

      <div className="zira-actions zira-no-print">
        <PrintButton label={t('rotation.print')} />
      </div>
      <p className="zira-statement">{t('app.supportStatement')}</p>
      <p className="zira-muted">v{card.model_version}</p>
    </div>
  );
}

type Translate = Awaited<ReturnType<typeof getTranslations>>;

function StrategyBlock({
  strategy,
  t,
  number,
  signed,
  cropLabel,
}: {
  strategy: RotationStrategy;
  t: Translate;
  number: (value: number | null, digits?: number) => string;
  signed: (value: number | null, digits?: number) => string;
  cropLabel: (key: string) => string;
}) {
  const m = strategy.metrics;
  const name = t(`rotation.strategy.${strategy.key}`);
  const diff = strategy.difference;
  return (
    <section className="zira-strategy" aria-label={name}>
      <h3 className="zira-subheading">{name}</h3>
      {m.valid === 0 ? (
        <p className="zira-muted">{t('rotation.metrics.noValid')}</p>
      ) : (
        <>
          <p className="zira-strategy-figure">
            {t('rotation.metrics.enough', { sufficient: m.sufficient, valid: m.valid })}
          </p>
          <p className="zira-muted">
            {t('rotation.metrics.range', { low: m.sufficient_low, high: m.sufficient_high })} ·{' '}
            {t('rotation.metrics.sown', { sown: m.sown, fallow: m.fallow })}
          </p>
        </>
      )}

      <div className="zira-season-strip" role="img" aria-label={t('rotation.seasons.aria', { name })}>
        {strategy.seasons.map((season) => {
          const state = seasonState(season);
          return (
            <span
              key={season.year}
              className={`zira-season zira-season--${state}`}
              title={`${season.year}: ${t(`rotation.seasons.${state}`)}${
                season.crop ? ` · ${cropLabel(season.crop)}` : ''
              }`}
            />
          );
        })}
      </div>

      <dl className="zira-metrics">
        <dt>{t('rotation.metrics.stress')}</dt>
        <dd>{number(m.stress_days_mean, 1)}</dd>
        <dt>{t('rotation.metrics.deficit')}</dt>
        <dd>{number(m.deficit_mean_mm, 0)}</dd>
        <dt>{t('rotation.metrics.irrigation')}</dt>
        <dd>{number(m.irrigation_need_mean_mm, 0)}</dd>
      </dl>

      {diff && (
        <p className="zira-muted">
          {t('rotation.metrics.diff')}:{' '}
          <Badge tone={diff.sufficient >= 0 ? 'success' : 'warning'}>
            {t('rotation.metrics.points', { value: signed(diff.share_points, 0) })}
          </Badge>{' '}
          · {signed(diff.deficit_mean_mm, 0)} mm
        </p>
      )}

      <dl className="zira-fieldlist">
        {TEXT_ROWS.map((row) => (
          <div key={row}>
            <dt>{t(`rotation.fields.${row}`)}</dt>
            <dd>{t(`rotation.text.${strategy.key}.${row}`)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
