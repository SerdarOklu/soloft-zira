import { Alert, Badge } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { MeadowBanner } from '@/components/illustrations';
import { Link } from '@/i18n/navigation';
import { ApiError, api } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/format';
import { ROTATION_PRESETS } from '@/lib/rotation';
import type { FieldOut, RotationComparison, RotationSeason, RotationStrategy } from '@/lib/types';

const KNOWN_ROTATIONS = new Set<string>(Object.values(ROTATION_PRESETS));
const TEXT_ROWS = ['rationale', 'evidence', 'benefit', 'gap', 'risk'] as const;

function seasonState(season: RotationSeason): 'sufficient' | 'short' | 'fallow' | 'heldBack' | 'invalid' {
  if (season.crop === null) return season.planned === null ? 'fallow' : 'heldBack';
  if (!season.valid) return 'invalid';
  return season.sufficient ? 'sufficient' : 'short';
}

/**
 * The farmer's view of the rotation comparison: the same three strategies and numbers as the
 * staff screen, as cards. No ranking is added and no option is called the best.
 */
export async function FarmerRotationContent({ params }: { params: { field?: string; rotation?: string } }) {
  const [t, locale, fields] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);

  const banner = (
    <header className="zira-farm-banner">
      <MeadowBanner />
      <div>
        <h1 className="zira-farm-title">{t('screens.myRotation.title')}</h1>
        <p className="zira-farm-lede">{t('screens.myRotation.description')}</p>
      </div>
    </header>
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack zira-farmer zira-farm zira-farm--wide">
        {banner}
        <p className="zira-farm-card">{t('farmerView.noFields')}</p>
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  const rotation =
    params.rotation && KNOWN_ROTATIONS.has(params.rotation)
      ? params.rotation
      : ROTATION_PRESETS.wheatFallow;
  const presetKey = (Object.keys(ROTATION_PRESETS) as (keyof typeof ROTATION_PRESETS)[]).find(
    (key) => ROTATION_PRESETS[key] === rotation,
  );

  const tabs =
    fields.length > 1 ? (
      <nav className="zira-farm-tabs" aria-label={t('rotation.form.field')}>
        {fields.map((candidate) => (
          <Link
            key={candidate.id}
            href={`/rotation?field=${candidate.id}`}
            aria-current={candidate.id === field.id ? 'page' : undefined}
          >
            {candidate.name}
          </Link>
        ))}
      </nav>
    ) : null;

  let card: RotationComparison;
  try {
    card = await api<RotationComparison>(
      `/fields/${encodeURIComponent(field.id)}/rotation?rotation=${encodeURIComponent(rotation)}`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && error.detail?.code) {
      const code = error.detail.code;
      const known = t.has(`rotation.errors.${code}`) ? code : 'generic';
      return (
        <div className="zira-stack zira-farmer zira-farm zira-farm--wide">
          {banner}
          {tabs}
          <Alert tone="warning">{t(`rotation.errors.${known}`)}</Alert>
        </div>
      );
    }
    throw error;
  }

  const number = (value: number | null, digits = 0) => formatNumber(value, locale, digits);
  const signed = (value: number | null, digits = 1) =>
    value === null ? '—' : `${value > 0 ? '+' : ''}${number(value, digits)}`;
  const cropLabel = (key: string) => (t.has(`crops.${key}`) ? t(`crops.${key}`) : key);

  return (
    <div className="zira-stack zira-farmer zira-farm zira-farm--wide">
      {banner}
      {tabs}

      <p className="zira-farm-meta">
        {t('rotation.summary', {
          field: field.name,
          count: card.seasons,
          first: formatDate(card.first_day, locale),
          last: formatDate(card.last_day, locale),
        })}
        {presetKey && ` · ${t('rotation.form.rotation')}: ${t(`rotation.form.presets.${presetKey}`)}`}
      </p>

      {card.provisional && (
        <Alert tone="warning" title={t('rotation.provisional.title')}>
          {t('rotation.provisional.body')}{' '}
          {card.provisional_sources.map((code) => t(`rotation.provisionalSources.${code}`)).join(', ')}.
        </Alert>
      )}

      <div className="zira-farm-strategies">
        {card.strategies.map((strategy) => (
          <StrategyCard
            key={strategy.key}
            strategy={strategy}
            t={t}
            number={number}
            signed={signed}
            cropLabel={cropLabel}
          />
        ))}
      </div>

      <p className="zira-farm-note">{t('myRotation.denominator')}</p>

      <section className="zira-farm-card" aria-labelledby="legend-title">
        <h2 id="legend-title">{t('rotation.seasons.title')}</h2>
        <ul className="zira-legend zira-season-legend">
          {(['sufficient', 'short', 'fallow', 'heldBack', 'invalid'] as const).map((state) => (
            <li key={state}>
              <span className={`zira-season zira-season--${state}`} />
              {t(`rotation.seasons.${state}`)}
            </li>
          ))}
        </ul>
      </section>

      <details className="zira-farm-card zira-farm-details">
        <summary>{t('rotation.assumptionsTitle')}</summary>
        <ul className="zira-list">
          {card.assumptions.map((code) => (
            <li key={code}>{t(`rotation.assumptions.${code}`)}</li>
          ))}
        </ul>
        {card.needs_signoff.length > 0 && (
          <p className="zira-farm-meta">
            {t('rotation.needsSignoff')}{' '}
            {card.needs_signoff
              .map((name) => (t.has(`waterVault.params.${name}`) ? t(`waterVault.params.${name}`) : name))
              .join(', ')}
            .
          </p>
        )}
      </details>

      <p className="zira-statement">{t('app.supportStatement')}</p>
      <p className="zira-farm-meta">v{card.model_version}</p>
    </div>
  );
}

type Translate = Awaited<ReturnType<typeof getTranslations>>;

function StrategyCard({
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
    <section className="zira-farm-card zira-farm-strategy" aria-label={name}>
      <h2>{name}</h2>
      {m.valid === 0 ? (
        <p className="zira-farm-meta">{t('rotation.metrics.noValid')}</p>
      ) : (
        <>
          <p className="zira-farm-figure">
            {t('rotation.metrics.enough', { sufficient: m.sufficient, valid: m.valid })}
          </p>
          <p className="zira-farm-meta">
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
        <p className="zira-farm-meta">
          {t('rotation.metrics.diff')}:{' '}
          <Badge tone={diff.sufficient >= 0 ? 'success' : 'warning'}>
            {t('rotation.metrics.points', { value: signed(diff.share_points, 0) })}
          </Badge>{' '}
          · {signed(diff.deficit_mean_mm, 0)} mm
        </p>
      )}

      <details className="zira-farm-details">
        <summary>{t('myRotation.detail')}</summary>
        <dl className="zira-fieldlist">
          {TEXT_ROWS.map((row) => (
            <div key={row}>
              <dt>{t(`rotation.fields.${row}`)}</dt>
              <dd>{t(`rotation.text.${strategy.key}.${row}`)}</dd>
            </div>
          ))}
        </dl>
      </details>
    </section>
  );
}
