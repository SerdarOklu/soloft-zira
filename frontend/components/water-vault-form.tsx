'use client';

import { Button, Field, Input, Select } from '@soloft/uds';
import { useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { useRouter } from '@/i18n/navigation';

interface Props {
  fields: { id: string; name: string; code: string }[];
  crops: { key: string; name_tr: string }[];
  field: string;
  crop: string;
  date: string;
}

/** Picks the field, the crop and a date; the page reads them from the address. */
export function WaterVaultForm({ fields, crops, field, crop, date }: Props) {
  const t = useTranslations('waterVault.form');
  const tCrops = useTranslations('crops');
  const router = useRouter();
  const [fieldId, setFieldId] = useState(field);
  const [cropKey, setCropKey] = useState(crop);
  const [day, setDay] = useState(date);

  function submit(event: FormEvent) {
    event.preventDefault();
    const query = new URLSearchParams({ field: fieldId, crop: cropKey });
    if (day) query.set('date', day);
    router.push(`/water-vault?${query.toString()}`);
  }

  return (
    <form className="zira-filters" onSubmit={submit}>
      <Field label={t('field')}>
        <Select value={fieldId} onChange={(event) => setFieldId(event.target.value)}>
          {fields.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} ({option.code})
            </option>
          ))}
        </Select>
      </Field>
      <Field label={t('crop')}>
        <Select value={cropKey} onChange={(event) => setCropKey(event.target.value)}>
          {crops.map((option) => (
            <option key={option.key} value={option.key}>
              {tCrops.has(option.key) ? tCrops(option.key) : option.name_tr}
            </option>
          ))}
        </Select>
      </Field>
      <Field label={t('date')} hint={t('dateHint')}>
        <Input type="date" value={day} onChange={(event) => setDay(event.target.value)} />
      </Field>
      <Button type="submit">{t('submit')}</Button>
    </form>
  );
}
