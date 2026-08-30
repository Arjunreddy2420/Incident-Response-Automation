export type IncidentStatus = "OPEN" | "ACKNOWLEDGED" | "INVESTIGATING" | "RESOLVED";
export type IncidentSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface Alert {
  id: string;
  incident_id: string;
  source: string;
  metric_name: string;
  threshold: number | null;
  current_value: number | null;
  alert_message: string | null;
  received_at: string;
}

export interface IncidentTimelineEntry {
  id: string;
  incident_id: string;
  event_type: string;
  actor: string | null;
  message: string | null;
  timestamp: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string | null;
  status: IncidentStatus;
  severity: IncidentSeverity;
  assigned_team: string | null;
  assigned_engineer: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  alert_count: number;
  mttr_minutes: number | null;
  tags: string[] | null;
}

export interface IncidentDetail extends Incident {
  alerts: Alert[];
  timeline: IncidentTimelineEntry[];
}

export interface IncidentCreateRequest {
  title: string;
  description?: string | null;
  severity?: IncidentSeverity;
  team: string;
}

export interface IncidentUpdateRequest {
  status?: IncidentStatus | null;
  assigned_engineer?: string | null;
  tags?: string[] | null;
}

export interface EscalationPolicy {
  id: string;
  team_name: string;
  severity_level: IncidentSeverity;
  on_call_engineer: string;
  backup_engineer: string | null;
  escalation_time_minutes: number;
  slack_channel: string | null;
}

export interface EscalationPolicyCreateRequest {
  team_name: string;
  severity: IncidentSeverity;
  on_call_engineer: string;
  backup_engineer?: string | null;
  escalation_time_minutes?: number;
  slack_channel?: string | null;
}

export interface EscalationPolicyUpdateRequest {
  on_call_engineer?: string;
  backup_engineer?: string | null;
  escalation_time_minutes?: number;
  slack_channel?: string | null;
}

export interface Metrics {
  total_incidents: number;
  open_incidents: number;
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
  avg_mttr_minutes: number | null;
}

export interface RunBook {
  id: string;
  team_name: string;
  metric_pattern: string | null;
  title: string;
  url: string;
  steps: string[];
}
