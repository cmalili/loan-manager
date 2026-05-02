import { Inbox } from "lucide-react";

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <Inbox aria-hidden="true" size={20} />
      <p>{message}</p>
    </div>
  );
}
