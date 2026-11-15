'use client';

import { Field, Select } from '@soloft/uds';
import { useTranslations } from 'next-intl';

import { useRouter } from '@/i18n/navigation';

interface Props {
  fields: { id: string; name: string; code: string }[];
  field: string;
}

/** Picks the field; the page reads it from the address. */
export function FieldMemoryForm({ fields, field }: Props) {
  const t = useTranslations('fieldMemory.form');
  const router = useRouter();

  return (
    <form className="zira-filters" onSubmit={(event) => event.preventDefault()}>
      <Field label={t('field')}>
        <Select
          value={field}
          onChange={(event) =>
            router.push(`/field-memory?${new URLSearchParams({ field: event.target.value })}`)
          }
        >
          {fields.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} ({option.code})
            </option>
          ))}
        </Select>
      </Field>
    </form>
  );
}
