import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { EscalationPolicy, IncidentSeverity } from "../api/types";
import { SeverityBadge } from "../components/SeverityBadge";

const SEVERITIES: IncidentSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

const emptyForm = {
  team_name: "",
  severity: "MEDIUM" as IncidentSeverity,
  on_call_engineer: "",
  backup_engineer: "",
  escalation_time_minutes: 30,
  slack_channel: "",
};

export function EscalationPolicies() {
  const [policies, setPolicies] = useState<EscalationPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    api
      .listEscalationPolicies()
      .then(setPolicies)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load policies"))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  function startEdit(policy: EscalationPolicy) {
    setEditingId(policy.id);
    setForm({
      team_name: policy.team_name,
      severity: policy.severity_level,
      on_call_engineer: policy.on_call_engineer,
      backup_engineer: policy.backup_engineer ?? "",
      escalation_time_minutes: policy.escalation_time_minutes,
      slack_channel: policy.slack_channel ?? "",
    });
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
    setFormError(null);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      if (editingId) {
        await api.updateEscalationPolicy(editingId, {
          on_call_engineer: form.on_call_engineer,
          backup_engineer: form.backup_engineer || null,
          escalation_time_minutes: form.escalation_time_minutes,
          slack_channel: form.slack_channel || null,
        });
      } else {
        await api.createEscalationPolicy({
          team_name: form.team_name,
          severity: form.severity,
          on_call_engineer: form.on_call_engineer,
          backup_engineer: form.backup_engineer || null,
          escalation_time_minutes: form.escalation_time_minutes,
          slack_channel: form.slack_channel || null,
        });
      }
      resetForm();
      load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to save policy");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>Escalation Policies</h1>

      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <table className="table">
          <thead>
            <tr>
              <th>Team</th>
              <th>Severity</th>
              <th>On-call</th>
              <th>Backup</th>
              <th>Escalation (min)</th>
              <th>Slack channel</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {policies.map((policy) => (
              <tr key={policy.id}>
                <td>{policy.team_name}</td>
                <td>
                  <SeverityBadge severity={policy.severity_level} />
                </td>
                <td>{policy.on_call_engineer}</td>
                <td>{policy.backup_engineer ?? "—"}</td>
                <td>{policy.escalation_time_minutes}</td>
                <td>{policy.slack_channel ?? "—"}</td>
                <td>
                  <button className="link-button" onClick={() => startEdit(policy)}>
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <section className="section">
        <h2>{editingId ? "Edit policy" : "New policy"}</h2>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Team name
            <input
              required
              disabled={!!editingId}
              value={form.team_name}
              onChange={(e) => setForm({ ...form, team_name: e.target.value })}
            />
          </label>
          <label>
            Severity
            <select
              disabled={!!editingId}
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value as IncidentSeverity })}
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            On-call engineer
            <input
              required
              value={form.on_call_engineer}
              onChange={(e) => setForm({ ...form, on_call_engineer: e.target.value })}
            />
          </label>
          <label>
            Backup engineer
            <input
              value={form.backup_engineer}
              onChange={(e) => setForm({ ...form, backup_engineer: e.target.value })}
            />
          </label>
          <label>
            Escalation time (minutes)
            <input
              type="number"
              min={1}
              value={form.escalation_time_minutes}
              onChange={(e) => setForm({ ...form, escalation_time_minutes: Number(e.target.value) })}
            />
          </label>
          <label>
            Slack channel
            <input
              value={form.slack_channel}
              onChange={(e) => setForm({ ...form, slack_channel: e.target.value })}
            />
          </label>

          {formError && <p className="error">{formError}</p>}

          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {editingId ? "Save changes" : "Create policy"}
            </button>
            {editingId && (
              <button type="button" className="secondary" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>
    </div>
  );
}
