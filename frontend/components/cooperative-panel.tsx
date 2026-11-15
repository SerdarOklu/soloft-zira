'use client';

import {
  Alert,
  Badge,
  Button,
  Field,
  Input,
  Section,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { useRouter } from '@/i18n/navigation';
import type { UserOut } from '@/lib/types';

type Notice = { tone: 'danger' | 'success'; text: string };

interface FieldRow {
  id: string;
  name: string;
  farmer_user_id: string | null;
}

/** The cooperative's farmers: create an account, close or open it, and link fields to farmers. */
export function CooperativePanel({ farmers, fields }: { farmers: UserOut[]; fields: FieldRow[] }) {
  const t = useTranslations('cooperative');
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  async function call(path: string, method: 'POST' | 'PATCH', body: unknown): Promise<boolean> {
    setBusy(true);
    setNotice(null);
    try {
      const response = await fetch(`/api/backend${path}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const json = (await response.json().catch(() => null)) as { detail?: { code?: string } } | null;
        const code = json?.detail?.code;
        setNotice({
          tone: 'danger',
          text: t(code && t.has(`errors.${code}`) ? `errors.${code}` : 'errors.generic'),
        });
        return false;
      }
      router.refresh();
      return true;
    } catch {
      setNotice({ tone: 'danger', text: t('errors.generic') });
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (await call('/users', 'POST', { name, email, password, role: 'farmer' })) {
      setName('');
      setEmail('');
      setPassword('');
      setNotice({ tone: 'success', text: t('create.done') });
    }
  }

  return (
    <div className="zira-stack">
      {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}

      <Section title={t('create.title')}>
        <form className="zira-filters" onSubmit={create}>
          <Field label={t('create.name')}>
            <Input value={name} onChange={(e) => setName(e.target.value)} maxLength={200} required />
          </Field>
          <Field label={t('create.email')}>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </Field>
          <Field label={t('create.password')} hint={t('create.passwordHint')}>
            <Input
              type="password"
              autoComplete="new-password"
              value={password}
              minLength={10}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Field>
          <Button type="submit" loading={busy}>
            {t('create.submit')}
          </Button>
        </form>
      </Section>

      <Section title={t('farmersTitle')}>
        {farmers.length === 0 ? (
          <p>{t('noFarmers')}</p>
        ) : (
          <TableContainer label={t('farmersTitle')} appearance="card">
            <Table density="compact">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>{t('columns.name')}</TableHeaderCell>
                  <TableHeaderCell>{t('columns.email')}</TableHeaderCell>
                  <TableHeaderCell align="end">{t('columns.fields')}</TableHeaderCell>
                  <TableHeaderCell>{t('columns.status')}</TableHeaderCell>
                  <TableHeaderCell>{t('columns.actions')}</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {farmers.map((farmer) => (
                  <TableRow key={farmer.id}>
                    <TableCell>{farmer.name}</TableCell>
                    <TableCell>{farmer.email}</TableCell>
                    <TableCell numeric>{farmer.field_count}</TableCell>
                    <TableCell>
                      <Badge tone={farmer.is_active ? 'success' : 'neutral'}>
                        {t(farmer.is_active ? 'active' : 'inactive')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() =>
                          void call(`/users/${farmer.id}`, 'PATCH', { is_active: !farmer.is_active })
                        }
                      >
                        {t(farmer.is_active ? 'deactivate' : 'activate')}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Section>

      <Section title={t('linkTitle')}>
        {fields.length === 0 ? (
          <p>{t('noFields')}</p>
        ) : (
          <TableContainer label={t('linkTitle')} appearance="card">
            <Table density="compact">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>{t('fieldColumns.field')}</TableHeaderCell>
                  <TableHeaderCell>{t('fieldColumns.farmer')}</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fields.map((field) => (
                  <TableRow key={field.id}>
                    <TableCell>{field.name}</TableCell>
                    <TableCell>
                      <Select
                        aria-label={`${t('fieldColumns.farmer')} ${field.name}`}
                        value={field.farmer_user_id ?? ''}
                        disabled={busy}
                        onChange={(event) =>
                          void call(`/fields/${field.id}/farmer`, 'PATCH', {
                            farmer_user_id: event.target.value || null,
                          })
                        }
                      >
                        <option value="">{t('unlinked')}</option>
                        {farmers
                          .filter((farmer) => farmer.is_active)
                          .map((farmer) => (
                            <option key={farmer.id} value={farmer.id}>
                              {farmer.name}
                            </option>
                          ))}
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        <p className="zira-muted">{t('linkHint')}</p>
      </Section>
    </div>
  );
}
