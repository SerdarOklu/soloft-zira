import { PageHeader } from '@soloft/uds';
import { getTranslations } from 'next-intl/server';

import { FieldForm } from '@/components/field-form';
import { GuardedScreen } from '@/components/guarded-screen';
import { api } from '@/lib/api';
import type { SoilOption } from '@/lib/types';

async function NewField() {
  const [t, soils] = await Promise.all([
    getTranslations('fields.form'),
    api<SoilOption[]>('/reference/soils'),
  ]);
  return (
    <div className="zira-stack">
      <PageHeader title={t('title')} description={t('description')} />
      <FieldForm soils={soils} />
    </div>
  );
}

export default function Page() {
  return (
    <GuardedScreen screen="fields">
      <NewField />
    </GuardedScreen>
  );
}
