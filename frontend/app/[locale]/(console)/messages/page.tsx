import { GuardedScreen } from '@/components/guarded-screen';
import { MessagesContent } from '@/components/messages-content';

export default function Page() {
  return (
    <GuardedScreen screen="messages">
      <MessagesContent />
    </GuardedScreen>
  );
}
