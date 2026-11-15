import { FarmerMessagesContent } from '@/components/farmer-messages-content';
import { GuardedScreen } from '@/components/guarded-screen';
import { MessagesContent } from '@/components/messages-content';
import { getSessionUser } from '@/lib/session';

export default async function Page() {
  // A farmer reads what was sent to them; the draft queue and approvals stay with the staff.
  const user = await getSessionUser();
  if (user?.role === 'farmer') {
    return (
      <GuardedScreen screen="myMessages">
        <FarmerMessagesContent />
      </GuardedScreen>
    );
  }
  return (
    <GuardedScreen screen="messages">
      <MessagesContent />
    </GuardedScreen>
  );
}
