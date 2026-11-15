'use client';

import {
  Alert,
  Badge,
  Button,
  Field,
  Input,
  Section,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { useRouter } from '@/i18n/navigation';
import { formatDateTime, formatNumber } from '@/lib/format';
import type { SensorStatus } from '@/lib/types';

type Notice = { tone: 'danger' | 'success'; text: string };

/** The field's sensor nodes and the calibration that decides whether they are trusted. */
export function SensorPanel({
  fieldId,
  status,
  canCalibrate,
}: {
  fieldId: string;
  status: SensorStatus;
  canCalibrate: boolean;
}) {
  const t = useTranslations('sensors');
  const locale = useLocale();
  const router = useRouter();
  const calibration = status.calibration;
  const [slope, setSlope] = useState(String(calibration?.slope ?? 1));
  const [intercept, setIntercept] = useState(String(calibration?.intercept ?? 0));
  const [thetaWp, setThetaWp] = useState(String(calibration?.theta_wp ?? ''));
  const [thetaFc, setThetaFc] = useState(String(calibration?.theta_fc ?? ''));
  const [note, setNote] = useState(calibration?.note ?? '');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const number = (value: number | null, digits = 2) => formatNumber(value, locale, digits);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const response = await fetch(`/api/backend/fields/${fieldId}/sensor-calibration`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slope: Number(slope),
          intercept: Number(intercept),
          theta_wp: Number(thetaWp),
          theta_fc: Number(thetaFc),
          note: note || null,
        }),
      });
      if (!response.ok) {
        setNotice({
          tone: 'danger',
          text: t(response.status === 422 ? 'calibration.errors.invalid' : 'calibration.errors.generic'),
        });
        return;
      }
      setNotice({ tone: 'success', text: t('calibration.saved') });
      router.refresh();
    } catch {
      setNotice({ tone: 'danger', text: t('calibration.errors.generic') });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title={t('title')}>
      <div className="zira-stack">
        <p className="zira-muted">{t('description')}</p>

        {status.nodes.length === 0 ? (
          <p>{t('noNodes')}</p>
        ) : (
          <>
            <TableContainer label={t('title')} appearance="card">
              <Table density="compact">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>{t('columns.node')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.lastSeen')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.status')}</TableHeaderCell>
                    <TableHeaderCell align="end">{t('columns.battery')}</TableHeaderCell>
                    <TableHeaderCell>{t('columns.readings')}</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {status.nodes.map((node) => (
                    <TableRow key={node.node_id}>
                      <TableCell>
                        {node.node_id}{' '}
                        {node.is_simulated && <Badge tone="neutral">{t('simulated')}</Badge>}
                      </TableCell>
                      <TableCell>{formatDateTime(node.last_seen, locale)}</TableCell>
                      <TableCell>
                        <Badge tone={node.status === 'active' ? 'success' : 'warning'}>
                          {t(`status.${node.status}`)}
                        </Badge>
                      </TableCell>
                      <TableCell numeric>{number(node.battery_v, 1)}</TableCell>
                      <TableCell>
                        {node.readings
                          .map(
                            (reading) =>
                              `${reading.depth_cm} cm: ${number(reading.vwc_calibrated ?? reading.vwc_raw, 3)}`,
                          )
                          .join(' · ')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <p className="zira-muted">{t('silentNote', { hours: status.silence_h })}</p>
          </>
        )}

        <h3 className="zira-subheading">{t('calibration.title')}</h3>
        {calibration ? (
          <p>
            {t('calibration.current', {
              date: formatDateTime(calibration.calibrated_at, locale),
              slope: number(calibration.slope, 2),
              intercept: number(calibration.intercept, 3),
              wp: number(calibration.theta_wp, 2),
              fc: number(calibration.theta_fc, 2),
            })}
          </p>
        ) : (
          <Alert tone="warning">{t('calibration.none')}</Alert>
        )}

        {canCalibrate ? (
          <form className="zira-filters" onSubmit={save}>
            <Field label={t('calibration.slope')}>
              <Input type="number" step="0.01" value={slope} onChange={(e) => setSlope(e.target.value)} required />
            </Field>
            <Field label={t('calibration.intercept')}>
              <Input type="number" step="0.001" value={intercept} onChange={(e) => setIntercept(e.target.value)} required />
            </Field>
            <Field label={t('calibration.thetaWp')}>
              <Input type="number" step="0.01" value={thetaWp} onChange={(e) => setThetaWp(e.target.value)} required />
            </Field>
            <Field label={t('calibration.thetaFc')}>
              <Input type="number" step="0.01" value={thetaFc} onChange={(e) => setThetaFc(e.target.value)} required />
            </Field>
            <Field label={t('calibration.note')}>
              <Input value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
            </Field>
            <Button type="submit" loading={busy}>
              {t('calibration.save')}
            </Button>
          </form>
        ) : (
          <p className="zira-muted">{t('calibration.readOnly')}</p>
        )}
        <p className="zira-muted">{t('calibration.hint')}</p>
        {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
        <p className="zira-muted">{t('simulator', { id: fieldId })}</p>
      </div>
    </Section>
  );
}
