import { CooperativeContent } from '@/components/cooperative-content';
import { GuardedScreen } from '@/components/guarded-screen';

export default function Page() {
  return (
    <GuardedScreen screen="settings">
      <CooperativeContent />
    </GuardedScreen>
  );
}
