import { FieldMemoryContent, type FieldMemoryParams } from '@/components/field-memory-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default async function Page({ searchParams }: { searchParams: Promise<FieldMemoryParams> }) {
  const params = await searchParams;
  return (
    <GuardedScreen screen="fieldMemory">
      <FieldMemoryContent params={params} />
    </GuardedScreen>
  );
}
