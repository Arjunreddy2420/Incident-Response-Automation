import type { IncidentSeverity } from "../api/types";

const CLASS_BY_SEVERITY: Record<IncidentSeverity, string> = {
  CRITICAL: "badge badge--critical",
  HIGH: "badge badge--high",
  MEDIUM: "badge badge--medium",
  LOW: "badge badge--low",
};

export function SeverityBadge({ severity }: { severity: IncidentSeverity }) {
  return <span className={CLASS_BY_SEVERITY[severity]}>{severity}</span>;
}
