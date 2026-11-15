import { FarmerContent } from '@/components/farmer-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default function Page() {
  return (
    <GuardedScreen screen="farmer">
      <FarmerContent />
    </GuardedScreen>
  );
}
