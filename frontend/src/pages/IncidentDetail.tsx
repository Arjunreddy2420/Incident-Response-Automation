import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { IncidentDetail as IncidentDetailType, RunBook } from "../api/types";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";

type RunbookState =
  | { kind: "loading" }
  | { kind: "found"; runbook: RunBook }
  | { kind: "none" }
  | { kind: "error"; message: string };

export function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<IncidentDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runbookState, setRunbookState] = useState<RunbookState>({ kind: "loading" });
  const [engineerName, setEngineerName] = useState("");
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionPending, setActionPending] = useState(false);

  function loadIncident(incidentId: string) {
    setLoading(true);
    setError(null);
    api
      .getIncident(incidentId)
      .then(setIncident)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load incident"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!id) return;
    loadIncident(id);
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setRunbookState({ kind: "loading" });
    api
      .getRunbookForIncident(id)
      .then((runbook) => setRunbookState({ kind: "found", runbook }))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setRunbookState({ kind: "none" });
        } else {
          setRunbookState({ kind: "error", message: err instanceof Error ? err.message : "Failed to load runbook" });
        }
      });
  }, [id]);

  async function handleAcknowledge() {
    if (!id || !engineerName.trim()) return;
    setActionPending(true);
    setActionError(null);
    try {
      await api.acknowledgeIncident(id, engineerName.trim());
      loadIncident(id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to acknowledge incident");
    } finally {
      setActionPending(false);
    }
  }

  async function handleResolve() {
    if (!id) return;
    setActionPending(true);
    setActionError(null);
    try {
      await api.resolveIncident(id, resolutionSummary.trim() || undefined);
      loadIncident(id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to resolve incident");
    } finally {
      setActionPending(false);
    }
  }

  if (loading) return <div className="page">Loading…</div>;
  if (error) return <div className="page error">{error}</div>;
  if (!incident) return null;

  const canAcknowledge = incident.status === "OPEN";
  const canResolve = incident.status !== "RESOLVED";

  return (
    <div className="page">
      <Link to="/" className="back-link">
        ← Back to incidents
      </Link>

      <div className="detail-header">
        <h1>{incident.title}</h1>
        <div className="detail-badges">
          <SeverityBadge severity={incident.severity} />
          <StatusBadge status={incident.status} />
        </div>
      </div>

      {incident.description && <p className="description">{incident.description}</p>}

      <div className="detail-grid">
        <div>
          <strong>Team</strong>
          <div>{incident.assigned_team ?? "—"}</div>
        </div>
        <div>
          <strong>Engineer</strong>
          <div>{incident.assigned_engineer ?? "Unassigned"}</div>
        </div>
        <div>
          <strong>Created</strong>
          <div>{new Date(incident.created_at).toLocaleString()}</div>
        </div>
        <div>
          <strong>Resolved</strong>
          <div>{incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : "—"}</div>
        </div>
        <div>
          <strong>MTTR</strong>
          <div>{incident.mttr_minutes != null ? `${incident.mttr_minutes} min` : "—"}</div>
        </div>
        <div>
          <strong>Alert count</strong>
          <div>{incident.alert_count}</div>
        </div>
      </div>

      {(canAcknowledge || canResolve) && (
        <div className="actions">
          {canAcknowledge && (
            <div className="action">
              <input
                placeholder="Your name"
                value={engineerName}
                onChange={(e) => setEngineerName(e.target.value)}
              />
              <button disabled={actionPending || !engineerName.trim()} onClick={handleAcknowledge}>
                Acknowledge
              </button>
            </div>
          )}
          {canResolve && (
            <div className="action">
              <input
                placeholder="Resolution summary (optional)"
                value={resolutionSummary}
                onChange={(e) => setResolutionSummary(e.target.value)}
              />
              <button disabled={actionPending} onClick={handleResolve}>
                Resolve
              </button>
            </div>
          )}
        </div>
      )}
      {actionError && <p className="error">{actionError}</p>}

      <section className="section">
        <h2>Runbook</h2>
        {runbookState.kind === "loading" && <p>Loading…</p>}
        {runbookState.kind === "none" && <p className="empty">No runbook linked for this incident.</p>}
        {runbookState.kind === "error" && <p className="error">{runbookState.message}</p>}
        {runbookState.kind === "found" && (
          <div className="runbook">
            <a href={runbookState.runbook.url} target="_blank" rel="noreferrer">
              {runbookState.runbook.title}
            </a>
            {runbookState.runbook.steps.length > 0 && (
              <ol className="runbook-steps">
                {runbookState.runbook.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            )}
          </div>
        )}
      </section>

      <section className="section">
        <h2>Alerts ({incident.alerts.length})</h2>
        {incident.alerts.length === 0 && <p className="empty">No alerts recorded.</p>}
        {incident.alerts.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Metric</th>
                <th>Threshold</th>
                <th>Current value</th>
                <th>Received</th>
              </tr>
            </thead>
            <tbody>
              {incident.alerts.map((alert) => (
                <tr key={alert.id}>
                  <td>{alert.source}</td>
                  <td>{alert.metric_name}</td>
                  <td>{alert.threshold ?? "—"}</td>
                  <td>{alert.current_value ?? "—"}</td>
                  <td>{new Date(alert.received_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="section">
        <h2>Timeline</h2>
        {incident.timeline.length === 0 && <p className="empty">No timeline events yet.</p>}
        {incident.timeline.length > 0 && (
          <ul className="timeline">
            {incident.timeline
              .slice()
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              .map((entry) => (
                <li key={entry.id}>
                  <span className="timeline-time">{new Date(entry.timestamp).toLocaleString()}</span>
                  <span className="timeline-type">{entry.event_type}</span>
                  {entry.actor && <span className="timeline-actor">{entry.actor}</span>}
                  {entry.message && <span className="timeline-message">{entry.message}</span>}
                </li>
              ))}
          </ul>
        )}
      </section>
    </div>
  );
}
