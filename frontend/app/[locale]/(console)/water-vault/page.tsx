import { FarmerWaterContent } from '@/components/farmer-water-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { WaterVaultContent, type WaterVaultParams } from '@/components/water-vault-content';
import { getSessionUser } from '@/lib/session';

export default async function Page({ searchParams }: { searchParams: Promise<WaterVaultParams> }) {
  const params = await searchParams;
  // A farmer reads the water in their field; calibration and regional checks stay with the staff.
  const user = await getSessionUser();
  if (user?.role === 'farmer') {
    return (
      <GuardedScreen screen="myWater">
        <FarmerWaterContent params={params} />
      </GuardedScreen>
    );
  }
  return (
    <GuardedScreen screen="waterVault">
      <WaterVaultContent params={params} />
    </GuardedScreen>
  );
}
