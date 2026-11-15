'use client';

import { Field, Select } from '@soloft/uds';
import { useTranslations } from 'next-intl';

import { useRouter } from '@/i18n/navigation';

interface Props {
  fields: { id: string; name: string; code: string }[];
  field: string;
  source: string;
}

/** Picks the field; the page reads it from the address. */
export function FieldMemoryForm({ fields, field, source }: Props) {
  const t = useTranslations('fieldMemory');
  const router = useRouter();

  return (
    <form className="zira-filters" onSubmit={(event) => event.preventDefault()}>
      <Field label={t('form.field')}>
        <Select
          value={field}
          onChange={(event) =>
            router.push(`/field-memory?${new URLSearchParams({ field: event.target.value, source })}`)
          }
        >
          {fields.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} ({option.code})
            </option>
          ))}
        </Select>
      </Field>
      <Field label={t('satellite')}>
        <Select
          value={source}
          onChange={(event) =>
            router.push(`/field-memory?${new URLSearchParams({ field, source: event.target.value })}`)
          }
        >
          {['auto', 'landsat', 'modis'].map((key) => (
            <option key={key} value={key}>
              {t(`sources.${key}`)}
            </option>
          ))}
        </Select>
      </Field>
    </form>
  );
}
