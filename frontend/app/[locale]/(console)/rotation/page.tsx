import { GuardedScreen } from '@/components/guarded-screen';
import { RotationContent, type RotationParams } from '@/components/rotation-content';

export default async function Page({ searchParams }: { searchParams: Promise<RotationParams> }) {
  const params = await searchParams;
  return (
    <GuardedScreen screen="rotation">
      <RotationContent params={params} />
    </GuardedScreen>
  );
}
