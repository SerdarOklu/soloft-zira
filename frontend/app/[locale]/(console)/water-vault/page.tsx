import { GuardedScreen } from '@/components/guarded-screen';
import { WaterVaultContent, type WaterVaultParams } from '@/components/water-vault-content';

export default async function Page({ searchParams }: { searchParams: Promise<WaterVaultParams> }) {
  const params = await searchParams;
  return (
    <GuardedScreen screen="waterVault">
      <WaterVaultContent params={params} />
    </GuardedScreen>
  );
}
