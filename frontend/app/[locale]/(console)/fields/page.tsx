import { FieldsContent } from '@/components/fields-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default function Page() {
  return (
    <GuardedScreen screen="fields">
      <FieldsContent />
    </GuardedScreen>
  );
}
