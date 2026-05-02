import { titleCase } from "@/lib/format";

const toneByStatus: Record<string, string> = {
  active: "success",
  paid: "success",
  closed: "success",
  pending: "neutral",
  draft: "neutral",
  inactive: "neutral",
  partially_paid: "warning",
  overdue: "danger",
  defaulted: "danger",
  cancelled: "danger",
  restructured: "warning",
  recorded: "success",
  reversed: "danger",
  voided: "neutral"
};

export function StatusBadge({ status }: { status: string }) {
  const tone = toneByStatus[status] ?? "neutral";
  return <span className={`status-badge ${tone}`}>{titleCase(status)}</span>;
}
