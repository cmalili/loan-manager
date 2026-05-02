import { AlertCircle, CheckCircle2 } from "lucide-react";

export function Notice({
  tone = "info",
  children
}: {
  tone?: "info" | "success" | "error";
  children: React.ReactNode;
}) {
  const Icon = tone === "success" ? CheckCircle2 : AlertCircle;
  return (
    <div className={`notice ${tone}`} role={tone === "error" ? "alert" : "status"}>
      <Icon aria-hidden="true" size={18} />
      <span>{children}</span>
    </div>
  );
}
