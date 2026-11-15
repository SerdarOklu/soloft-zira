import { FieldDetailContent } from '@/components/field-detail-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <GuardedScreen screen="fields">
      <FieldDetailContent id={id} />
    </GuardedScreen>
  );
}
