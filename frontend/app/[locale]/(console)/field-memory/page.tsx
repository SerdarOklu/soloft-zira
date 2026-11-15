import { FarmerHistoryContent } from '@/components/farmer-history-content';
import { FieldMemoryContent, type FieldMemoryParams } from '@/components/field-memory-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { getSessionUser } from '@/lib/session';

export default async function Page({ searchParams }: { searchParams: Promise<FieldMemoryParams> }) {
  const params = await searchParams;
  // A farmer reads the history; fetching and confirming it stay with the staff screen.
  const user = await getSessionUser();
  if (user?.role === 'farmer') {
    return (
      <GuardedScreen screen="myHistory">
        <FarmerHistoryContent params={params} />
      </GuardedScreen>
    );
  }
  return (
    <GuardedScreen screen="fieldMemory">
      <FieldMemoryContent params={params} />
    </GuardedScreen>
  );
}
