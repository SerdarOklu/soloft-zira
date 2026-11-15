'use client';

import { Alert, Button, Field, Input, Select } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { FieldMap } from '@/components/field-map';
import { useRouter } from '@/i18n/navigation';
import { formatNumber } from '@/lib/format';
import { parseLatLon, toGeoJsonPolygon, type LonLat } from '@/lib/geometry';
import type { SoilOption, WaterRegime } from '@/lib/types';

const REGIMES: WaterRegime[] = ['rainfed', 'irrigated'];

export function FieldForm({ soils }: { soils: SoilOption[] }) {
  const t = useTranslations('fields.form');
  const tSoils = useTranslations('soils');
  const tRegimes = useTranslations('regimes');
  const locale = useLocale();
  const router = useRouter();

  const [name, setName] = useState('');
  const [region, setRegion] = useState('');
  const [regime, setRegime] = useState<WaterRegime>('rainfed');
  const [soil, setSoil] = useState('');
  const [corners, setCorners] = useState<LonLat[]>([]);
  const [position, setPosition] = useState('');
  const [positionError, setPositionError] = useState(false);
  const [flyTo, setFlyTo] = useState<{ lat: number; lon: number; nonce: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const soilLabel = (option: SoilOption) =>
    tSoils.has(option.key) ? tSoils(option.key) : option.name_tr;
  const chosen = soils.find((option) => option.key === soil);

  function goTo() {
    const parsed = parseLatLon(position);
    setPositionError(parsed === null);
    if (parsed) setFlyTo({ ...parsed, nonce: Date.now() });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!name.trim()) return setError(t('errors.needName'));
    if (!soil) return setError(t('errors.needSoil'));
    const geometry = toGeoJsonPolygon(corners);
    if (!geometry) return setError(t('errors.needPolygon'));

    setBusy(true);
    try {
      const response = await fetch('/api/backend/fields', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          region: region.trim() || null,
          water_regime: regime,
          soil_texture: soil,
          geometry,
        }),
      });
      if (response.status === 201) {
        const created = (await response.json()) as { id: string };
        router.push(`/fields/${created.id}`);
        return;
      }
      const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
      const crossing = typeof body?.detail === 'string' && body.detail.includes('edges must not cross');
      setError(crossing ? t('errors.invalidPolygon') : t('errors.generic'));
    } catch {
      setError(t('errors.unreachable'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="zira-stack" onSubmit={submit} noValidate>
      <div className="zira-form">
        <Field label={t('name')} required>
          <Input value={name} onChange={(event) => setName(event.target.value)} maxLength={200} />
        </Field>
        <Field label={t('region')}>
          <Input value={region} onChange={(event) => setRegion(event.target.value)} maxLength={200} />
        </Field>
        <Field label={t('regime')} required>
          <Select value={regime} onChange={(event) => setRegime(event.target.value as WaterRegime)}>
            {REGIMES.map((value) => (
              <option key={value} value={value}>
                {tRegimes(value)}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label={t('soil')}
          required
          hint={
            chosen
              ? t('soilHint', {
                  low: formatNumber(chosen.taw_mm_per_m[0], locale, 0),
                  high: formatNumber(chosen.taw_mm_per_m[1], locale, 0),
                })
              : undefined
          }
        >
          <Select value={soil} onChange={(event) => setSoil(event.target.value)}>
            <option value="">{t('soilChoose')}</option>
            {soils.map((option) => (
              <option key={option.key} value={option.key}>
                {soilLabel(option)}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div className="zira-stack">
        <div>
          <h2 className="zira-subheading">{t('map')}</h2>
          <p className="zira-muted">{t('mapHint')}</p>
        </div>

        <div className="zira-form">
          <Field label={t('goTo')} hint={t('goToHint')} error={positionError ? t('goToError') : undefined}>
            <Input
              value={position}
              onChange={(event) => setPosition(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault();
                  goTo();
                }
              }}
              inputMode="decimal"
            />
          </Field>
          <div className="zira-actions">
            <Button type="button" variant="secondary" size="sm" onClick={goTo}>
              {t('goToButton')}
            </Button>
          </div>
        </div>

        <FieldMap
          mode="draw"
          ariaLabel={t('mapAria')}
          corners={corners}
          onAddCorner={(lon, lat) => setCorners((current) => [...current, [lon, lat]])}
          flyTo={flyTo}
          className="zira-map--tall"
        />

        <div className="zira-actions">
          <span className="zira-muted" aria-live="polite">
            {t('points', { count: corners.length })}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={corners.length === 0}
            onClick={() => setCorners((current) => current.slice(0, -1))}
          >
            {t('undo')}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={corners.length === 0}
            onClick={() => setCorners([])}
          >
            {t('clear')}
          </Button>
        </div>
      </div>

      {error && <Alert tone="danger">{error}</Alert>}

      <div className="zira-actions">
        <Button type="submit" loading={busy}>
          {t('submit')}
        </Button>
        <Button href="/fields" variant="ghost">
          {t('cancel')}
        </Button>
      </div>
    </form>
  );
}
