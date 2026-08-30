import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Incident, IncidentSeverity, IncidentStatus } from "../api/types";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";

const STATUSES: IncidentStatus[] = ["OPEN", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"];
const SEVERITIES: IncidentSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

export function Dashboard() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<IncidentStatus | "">("");
  const [severity, setSeverity] = useState<IncidentSeverity | "">("");
  const [team, setTeam] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .listIncidents({
        status: status || undefined,
        severity: severity || undefined,
        team: team || undefined,
      })
      .then((data) => {
        if (!cancelled) setIncidents(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load incidents");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [status, severity, team]);

  return (
    <div className="page">
      <h1>Incidents</h1>

      <div className="filters">
        <select value={status} onChange={(e) => setStatus(e.target.value as IncidentStatus | "")}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select value={severity} onChange={(e) => setSeverity(e.target.value as IncidentSeverity | "")}>
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <input placeholder="Filter by team" value={team} onChange={(e) => setTeam(e.target.value)} />
      </div>

      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && incidents.length === 0 && <p className="empty">No incidents match these filters.</p>}

      {!loading && !error && incidents.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Team</th>
              <th>Alerts</th>
              <th>Created</th>
              <th>MTTR</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id}>
                <td>
                  <Link to={`/incidents/${incident.id}`}>{incident.title}</Link>
                </td>
                <td>
                  <SeverityBadge severity={incident.severity} />
                </td>
                <td>
                  <StatusBadge status={incident.status} />
                </td>
                <td>{incident.assigned_team ?? "—"}</td>
                <td>{incident.alert_count}</td>
                <td>{new Date(incident.created_at).toLocaleString()}</td>
                <td>{incident.mttr_minutes != null ? `${incident.mttr_minutes} min` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
