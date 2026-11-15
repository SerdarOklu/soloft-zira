import { PageHeader } from '@soloft/uds';
import { getTranslations } from 'next-intl/server';

import { CooperativePanel } from '@/components/cooperative-panel';
import { api } from '@/lib/api';
import type { FieldOut, UserOut } from '@/lib/types';

/** Farmer accounts and the link between fields and farmers (cooperative user or admin). */
export async function CooperativeContent() {
  const [t, users, fields] = await Promise.all([
    getTranslations(),
    api<UserOut[]>('/users'),
    api<FieldOut[]>('/fields'),
  ]);

  return (
    <div className="zira-stack">
      <PageHeader title={t('screens.settings.title')} description={t('screens.settings.description')} />
      <CooperativePanel
        farmers={users.filter((user) => user.role === 'farmer')}
        fields={fields.map(({ id, name, farmer_user_id }) => ({ id, name, farmer_user_id }))}
      />
      <p className="zira-statement">{t('app.supportStatement')}</p>
    </div>
  );
}
