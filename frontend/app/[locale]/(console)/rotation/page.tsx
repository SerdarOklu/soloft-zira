import { FarmerRotationContent } from '@/components/farmer-rotation-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { RotationContent, type RotationParams } from '@/components/rotation-content';
import { getSessionUser } from '@/lib/session';

export default async function Page({ searchParams }: { searchParams: Promise<RotationParams> }) {
  const params = await searchParams;
  // A farmer reads the comparison as cards; the form and the print view stay with the staff.
  const user = await getSessionUser();
  if (user?.role === 'farmer') {
    return (
      <GuardedScreen screen="myRotation">
        <FarmerRotationContent params={params} />
      </GuardedScreen>
    );
  }
  return (
    <GuardedScreen screen="rotation">
      <RotationContent params={params} />
    </GuardedScreen>
  );
}
