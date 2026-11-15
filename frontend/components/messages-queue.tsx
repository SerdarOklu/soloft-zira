'use client';

import { Alert, Badge, Button, Field, Input, Select } from '@soloft/uds';
import { useLocale, useTranslations } from 'next-intl';
import { useState } from 'react';

import { useRouter } from '@/i18n/navigation';
import { formatDate } from '@/lib/format';
import type { DraftStatus, MessageDraft } from '@/lib/types';

const STATUSES: DraftStatus[] = ['pending', 'approved', 'failed', 'sent', 'rejected'];
const TONES: Record<DraftStatus, 'neutral' | 'primary' | 'success' | 'warning' | 'danger'> = {
  pending: 'warning',
  approved: 'primary',
  sent: 'success',
  rejected: 'neutral',
  failed: 'danger',
};

type Notice = { tone: 'danger' | 'success' | 'warning'; text: string };

interface Props {
  drafts: MessageDraft[];
  fields: { id: string; name: string }[];
  gatewayConfigured: boolean;
  defaultYear: number;
  canReview: boolean;
}

/** The approval queue (left) and the farmer's phone (right). Nothing is sent before approval. */
export function MessagesQueue({ drafts, fields, gatewayConfigured, defaultYear, canReview }: Props) {
  const t = useTranslations('messages');
  const locale = useLocale();
  const router = useRouter();

  const [filter, setFilter] = useState<DraftStatus | 'all'>('pending');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [fieldId, setFieldId] = useState(fields[0]?.id ?? '');
  const [year, setYear] = useState(String(defaultYear));
  const [language, setLanguage] = useState(locale === 'en' ? 'en' : 'tr');
  const [generatePhone, setGeneratePhone] = useState('');
  const [phoneEdits, setPhoneEdits] = useState<Record<string, string>>({});
  const [bodyEdits, setBodyEdits] = useState<Record<string, string>>({});

  const shown = drafts.filter((draft) => filter === 'all' || draft.status === filter);
  const selected = drafts.find((draft) => draft.id === selectedId) ?? shown[0] ?? null;
  const body = selected ? (bodyEdits[selected.id] ?? selected.body) : '';
  const phone = selected ? (phoneEdits[selected.id] ?? '') : '';
  const open = selected !== null && (selected.status === 'pending' || selected.status === 'failed');

  const message = (code: string, detail: Record<string, unknown> = {}) => {
    const values: Record<string, string> = {};
    for (const key of ['first_date', 'last_date']) {
      const raw = detail[key];
      if (typeof raw === 'string') values[key.replace('_date', '')] = formatDate(raw, locale);
    }
    return t.has(`errors.${code}`) ? t(`errors.${code}`, values) : t('errors.generic');
  };

  async function call(path: string, method: 'POST' | 'PATCH', payload: unknown) {
    setBusy(true);
    setNotice(null);
    try {
      const response = await fetch(`/api/backend${path}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload ?? {}),
      });
      const json = (await response.json().catch(() => null)) as {
        detail?: { code?: string; [key: string]: unknown };
      } | null;
      if (!response.ok) {
        setNotice({ tone: 'danger', text: message(json?.detail?.code ?? 'generic', json?.detail) });
        return null;
      }
      return json;
    } catch {
      setNotice({ tone: 'danger', text: t('errors.generic') });
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    const result = (await call(`/fields/${fieldId}/messages/generate`, 'POST', {
      season_year: Number(year),
      locale: language,
      recipient_phone: generatePhone || null,
    })) as { created: number; skipped: number } | null;
    if (result) {
      setNotice({
        tone: 'success',
        text: t('generate.result', { created: result.created, skipped: result.skipped }),
      });
      router.refresh();
    }
  }

  async function act(kind: 'approve' | 'reject' | 'send') {
    if (!selected) return;
    if (kind === 'approve' && (bodyEdits[selected.id] ?? selected.body) !== selected.body) {
      const saved = await call(`/messages/${selected.id}`, 'PATCH', { body });
      if (!saved) return;
    }
    const result = (await call(
      `/messages/${selected.id}/${kind}`,
      'POST',
      kind === 'approve' && phone ? { recipient_phone: phone } : {},
    )) as MessageDraft | null;
    if (result) {
      setNotice(
        result.error
          ? { tone: 'warning', text: message(result.error) }
          : { tone: 'success', text: t(`status.${result.status}`) },
      );
      router.refresh();
    }
  }

  async function saveText() {
    if (!selected) return;
    if (await call(`/messages/${selected.id}`, 'PATCH', { body, recipient_phone: phone || undefined })) {
      setNotice({ tone: 'success', text: t('actions.save') });
      router.refresh();
    }
  }

  return (
    <div className="zira-stack">
      <Alert tone={gatewayConfigured ? 'info' : 'warning'}>
        {t(gatewayConfigured ? 'gateway.on' : 'gateway.off')}
      </Alert>

      {canReview && fields.length > 0 && (
        <form
          className="zira-filters"
          onSubmit={(event) => {
            event.preventDefault();
            void generate();
          }}
        >
          <Field label={t('generate.field')}>
            <Select value={fieldId} onChange={(event) => setFieldId(event.target.value)}>
              {fields.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={t('generate.year')}>
            <Input
              type="number"
              min={1990}
              max={2100}
              value={year}
              onChange={(event) => setYear(event.target.value)}
            />
          </Field>
          <Field label={t('generate.language')}>
            <Select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="tr">Türkçe</option>
              <option value="en">English</option>
            </Select>
          </Field>
          <Field label={t('generate.phone')} hint={t('generate.phoneHint')}>
            <Input
              type="tel"
              inputMode="tel"
              autoComplete="off"
              value={generatePhone}
              onChange={(event) => setGeneratePhone(event.target.value)}
            />
          </Field>
          <Button type="submit" disabled={busy}>
            {t('generate.submit')}
          </Button>
        </form>
      )}

      {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}

      <div className="zira-grid-2">
        <section aria-label={t('queue.title')}>
          <h3 className="zira-subheading">{t('queue.title')}</h3>
          <div className="zira-actions" role="group" aria-label={t('queue.title')}>
            {(['all', ...STATUSES] as const).map((status) => (
              <Button
                key={status}
                type="button"
                size="sm"
                variant={filter === status ? 'primary' : 'secondary'}
                onClick={() => setFilter(status)}
              >
                {status === 'all' ? t('queue.all') : t(`status.${status}`)} (
                {status === 'all' ? drafts.length : drafts.filter((d) => d.status === status).length})
              </Button>
            ))}
          </div>
          {shown.length === 0 ? (
            <p className="zira-muted">{t('queue.empty')}</p>
          ) : (
            <ul className="zira-draft-list">
              {shown.map((draft) => (
                <li key={draft.id}>
                  <button
                    type="button"
                    className="zira-draft"
                    aria-pressed={selected?.id === draft.id}
                    onClick={() => setSelectedId(draft.id)}
                  >
                    <span className="zira-draft-head">
                      <strong>
                        {t.has(`events.${draft.event_type}`)
                          ? t(`events.${draft.event_type}`)
                          : draft.event_type}
                      </strong>
                      <Badge tone={TONES[draft.status]}>{t(`status.${draft.status}`)}</Badge>
                    </span>
                    <span className="zira-muted">
                      {draft.field_name} · {formatDate(draft.event_date, locale)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-label={t('preview.title')}>
          <h3 className="zira-subheading">{t('preview.title')}</h3>
          {selected ? (
            <div className="zira-phone">
              <p className="zira-muted">
                {t('preview.to')}: {selected.recipient_hint ?? t('preview.noRecipient')}
              </p>
              {open && canReview ? (
                <textarea
                  className="zira-bubble zira-bubble--edit"
                  rows={9}
                  value={body}
                  aria-label={t('preview.title')}
                  onChange={(event) =>
                    setBodyEdits((current) => ({ ...current, [selected.id]: event.target.value }))
                  }
                />
              ) : (
                <div className="zira-bubble">{selected.body}</div>
              )}

              {selected.error && (
                <Alert tone="warning">{message(selected.error)}</Alert>
              )}

              {open && canReview && (
                <>
                  <Field label={t('actions.phone')} hint={t('generate.phoneHint')}>
                    <Input
                      type="tel"
                      inputMode="tel"
                      autoComplete="off"
                      placeholder={selected.recipient_hint ?? ''}
                      value={phone}
                      onChange={(event) =>
                        setPhoneEdits((current) => ({ ...current, [selected.id]: event.target.value }))
                      }
                    />
                  </Field>
                  <div className="zira-actions">
                    <Button type="button" disabled={busy} onClick={() => void act('approve')}>
                      {t('actions.approve')}
                    </Button>
                    <Button type="button" variant="secondary" disabled={busy} onClick={() => void saveText()}>
                      {t('actions.save')}
                    </Button>
                    <Button type="button" variant="secondary" disabled={busy} onClick={() => void act('reject')}>
                      {t('actions.reject')}
                    </Button>
                  </div>
                </>
              )}
              {selected.status === 'approved' && canReview && (
                <div className="zira-actions">
                  <Button type="button" disabled={busy} onClick={() => void act('send')}>
                    {t('actions.retry')}
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <p className="zira-muted">{t('queue.empty')}</p>
          )}
        </section>
      </div>

      <p className="zira-statement">{t('support')}</p>
    </div>
  );
}
