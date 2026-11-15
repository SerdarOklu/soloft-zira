import {
  Badge,
  Button,
  EmptyState,
  PageHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { Link } from '@/i18n/navigation';
import { api } from '@/lib/api';
import { formatNumber } from '@/lib/format';
import type { FieldOut } from '@/lib/types';

export async function FieldsContent() {
  const [t, locale, fields] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);

  return (
    <div className="zira-stack">
      <PageHeader
        title={t('screens.fields.title')}
        description={t('screens.fields.description')}
        actions={<Button href="/fields/new">{t('fields.add')}</Button>}
      />

      {fields.length === 0 ? (
        <EmptyState
          appearance="framed"
          title={t('fields.emptyTitle')}
          description={t('fields.emptyDescription')}
          locale={locale === 'en' ? 'en' : 'tr'}
          actions={<Button href="/fields/new">{t('fields.add')}</Button>}
        />
      ) : (
        <TableContainer label={t('screens.fields.title')} appearance="card">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>{t('fields.columns.name')}</TableHeaderCell>
                <TableHeaderCell>{t('fields.columns.region')}</TableHeaderCell>
                <TableHeaderCell align="end">{t('fields.columns.area')}</TableHeaderCell>
                <TableHeaderCell>{t('fields.columns.soil')}</TableHeaderCell>
                <TableHeaderCell>{t('fields.columns.regime')}</TableHeaderCell>
                <TableHeaderCell>{t('fields.columns.data')}</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {fields.map((field) => (
                <TableRow key={field.id}>
                  <TableCell secondary={field.code}>
                    <Link href={`/fields/${field.id}`}>{field.name}</Link>
                  </TableCell>
                  <TableCell>{field.region ?? '—'}</TableCell>
                  <TableCell numeric>
                    {field.area_ha === null ? '—' : `${formatNumber(field.area_ha, locale, 1)} ha`}
                  </TableCell>
                  <TableCell>
                    {field.soil_texture && t.has(`soils.${field.soil_texture}`)
                      ? t(`soils.${field.soil_texture}`)
                      : (field.soil_texture ?? '—')}
                  </TableCell>
                  <TableCell>{field.water_regime ? t(`regimes.${field.water_regime}`) : '—'}</TableCell>
                  <TableCell>
                    {field.weather_days > 0 ? (
                      <Badge tone="success" dot>
                        {t('fields.dataDays', { days: field.weather_days })}
                      </Badge>
                    ) : (
                      <Badge tone="warning" dot>
                        {t('fields.dataMissing')}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
