import { Button, EmptyState, PageHeader } from '@soloft/uds';
import { getLocale, getTranslations } from 'next-intl/server';

import { FieldMemoryForm } from '@/components/field-memory-form';
import { FieldMemoryPanel } from '@/components/field-memory-panel';
import { api } from '@/lib/api';
import type { FieldMemory, FieldOut } from '@/lib/types';

export interface FieldMemoryParams {
  field?: string;
  source?: string;
}

/** Was the field cropped or fallow in each of the last seasons? From MODIS, confirmed by a person. */
export async function FieldMemoryContent({ params }: { params: FieldMemoryParams }) {
  const [t, locale, fields] = await Promise.all([
    getTranslations(),
    getLocale(),
    api<FieldOut[]>('/fields'),
  ]);

  const header = (
    <PageHeader
      title={t('screens.fieldMemory.title')}
      description={t('screens.fieldMemory.description')}
    />
  );

  if (fields.length === 0) {
    return (
      <div className="zira-stack">
        {header}
        <EmptyState
          appearance="framed"
          title={t('fieldMemory.noFieldsTitle')}
          description={t('fieldMemory.noFieldsDescription')}
          locale={locale === 'en' ? 'en' : 'tr'}
          actions={<Button href="/fields/new">{t('fieldMemory.addField')}</Button>}
        />
      </div>
    );
  }

  const field = fields.find((candidate) => candidate.id === params.field) ?? fields[0];
  const source = ['modis', 'landsat'].includes(params.source ?? '') ? params.source : 'auto';
  const memory = await api<FieldMemory>(
    `/fields/${encodeURIComponent(field.id)}/field-memory?source=${source}`,
  );

  return (
    <div className="zira-stack">
      {header}
      <FieldMemoryForm
        fields={fields.map(({ id, name, code }) => ({ id, name, code }))}
        field={field.id}
        source={source ?? 'auto'}
      />
      <FieldMemoryPanel fieldId={field.id} memory={memory} />
      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
