import { DataCenterContent } from '@/components/data-center-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default function Page() {
  return (
    <GuardedScreen screen="dataCenter">
      <DataCenterContent />
    </GuardedScreen>
  );
}
