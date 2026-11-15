'use client';

import { Button, Field, Select } from '@soloft/uds';
import { useTranslations } from 'next-intl';
import { useState, type FormEvent } from 'react';

import { useRouter } from '@/i18n/navigation';
import { ROTATION_PRESETS } from '@/lib/rotation';

interface Props {
  fields: { id: string; name: string; code: string }[];
  field: string;
  rotation: string;
}

/** Picks the field and the current rotation; the page reads them from the address. */
export function RotationForm({ fields, field, rotation }: Props) {
  const t = useTranslations('rotation.form');
  const router = useRouter();
  const [fieldId, setFieldId] = useState(field);
  const [value, setValue] = useState(rotation);

  function submit(event: FormEvent) {
    event.preventDefault();
    router.push(`/rotation?${new URLSearchParams({ field: fieldId, rotation: value }).toString()}`);
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
      <Field label={t('rotation')}>
        <Select value={value} onChange={(event) => setValue(event.target.value)}>
          {(Object.keys(ROTATION_PRESETS) as (keyof typeof ROTATION_PRESETS)[]).map((key) => (
            <option key={key} value={ROTATION_PRESETS[key]}>
              {t(`presets.${key}`)}
            </option>
          ))}
        </Select>
      </Field>
      <Button type="submit">{t('submit')}</Button>
    </form>
  );
}
