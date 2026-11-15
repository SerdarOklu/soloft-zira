'use client';

import { FieldMap, type MapMarker } from '@/components/field-map';
import { useRouter } from '@/i18n/navigation';

/** The map on the overview: a click on a field opens it. */
export function DashboardMap({ markers, ariaLabel }: { markers: MapMarker[]; ariaLabel: string }) {
  const router = useRouter();
  return (
    <FieldMap
      mode="view"
      ariaLabel={ariaLabel}
      markers={markers}
      onSelectMarker={(id) => router.push(`/fields/${id}`)}
    />
  );
}
