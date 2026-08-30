import type {
  EscalationPolicy,
  EscalationPolicyCreateRequest,
  EscalationPolicyUpdateRequest,
  Incident,
  IncidentCreateRequest,
  IncidentDetail,
  IncidentSeverity,
  IncidentStatus,
  IncidentUpdateRequest,
  Metrics,
  RunBook,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export interface IncidentListFilters {
  status?: IncidentStatus;
  severity?: IncidentSeverity;
  team?: string;
}

function buildQuery(params: IncidentListFilters): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  metrics: () => request<Metrics>("/metrics"),

  listIncidents: (filters: IncidentListFilters = {}) =>
    request<Incident[]>(`/incidents${buildQuery(filters)}`),

  getIncident: (id: string) => request<IncidentDetail>(`/incidents/${id}`),

  createIncident: (payload: IncidentCreateRequest) =>
    request<{ id: string; created_at: string }>("/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateIncident: (id: string, payload: IncidentUpdateRequest) =>
    request<Incident>(`/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  acknowledgeIncident: (id: string, engineerName: string) =>
    request<Incident>(`/incidents/${id}/acknowledge`, {
      method: "POST",
      body: JSON.stringify({ engineer_name: engineerName }),
    }),

  resolveIncident: (id: string, resolutionSummary?: string) =>
    request<Incident>(`/incidents/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution_summary: resolutionSummary ?? null }),
    }),

  getRunbookForIncident: (id: string) => request<RunBook>(`/incidents/${id}/runbook`),

  listEscalationPolicies: () => request<EscalationPolicy[]>("/escalation-policies"),

  createEscalationPolicy: (payload: EscalationPolicyCreateRequest) =>
    request<EscalationPolicy>("/escalation-policies", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateEscalationPolicy: (id: string, payload: EscalationPolicyUpdateRequest) =>
    request<EscalationPolicy>(`/escalation-policies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};
