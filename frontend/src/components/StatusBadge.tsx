import type { IncidentStatus } from "../api/types";

const CLASS_BY_STATUS: Record<IncidentStatus, string> = {
  OPEN: "badge badge--open",
  ACKNOWLEDGED: "badge badge--acknowledged",
  INVESTIGATING: "badge badge--investigating",
  RESOLVED: "badge badge--resolved",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  return <span className={CLASS_BY_STATUS[status]}>{status}</span>;
}
