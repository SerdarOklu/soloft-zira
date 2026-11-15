import { DashboardContent } from '@/components/dashboard-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default function Page() {
  return (
    <GuardedScreen screen="dashboard">
      <DashboardContent />
    </GuardedScreen>
  );
}
