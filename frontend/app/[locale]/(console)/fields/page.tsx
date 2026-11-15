import { FarmerFieldsContent } from '@/components/farmer-fields-content';
import { FieldsContent } from '@/components/fields-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { getSessionUser } from '@/lib/session';

export default async function Page() {
  // A farmer gets a read-only card list; staff keep the table and the add button.
  const user = await getSessionUser();
  if (user?.role === 'farmer') {
    return (
      <GuardedScreen screen="myFields">
        <FarmerFieldsContent />
      </GuardedScreen>
    );
  }
  return (
    <GuardedScreen screen="fields">
      <FieldsContent />
    </GuardedScreen>
  );
}
