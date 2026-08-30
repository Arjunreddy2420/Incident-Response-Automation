import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Metrics as MetricsType } from "../api/types";

export function Metrics() {
  const [metrics, setMetrics] = useState<MetricsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .metrics()
      .then(setMetrics)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load metrics"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page">Loading…</div>;
  if (error) return <div className="page error">{error}</div>;
  if (!metrics) return null;

  const maxStatusCount = Math.max(1, ...Object.values(metrics.by_status));
  const maxSeverityCount = Math.max(1, ...Object.values(metrics.by_severity));

  return (
    <div className="page">
      <h1>Metrics</h1>

      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{metrics.total_incidents}</div>
          <div className="stat-label">Total incidents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{metrics.open_incidents}</div>
          <div className="stat-label">Open incidents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {metrics.avg_mttr_minutes != null ? `${metrics.avg_mttr_minutes} min` : "—"}
          </div>
          <div className="stat-label">Avg. MTTR</div>
        </div>
      </div>

      <section className="section">
        <h2>By status</h2>
        <div className="bars">
          {Object.entries(metrics.by_status).map(([status, count]) => (
            <div className="bar-row" key={status}>
              <span className="bar-label">{status}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(count / maxStatusCount) * 100}%` }} />
              </div>
              <span className="bar-count">{count}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>By severity</h2>
        <div className="bars">
          {Object.entries(metrics.by_severity).map(([severity, count]) => (
            <div className="bar-row" key={severity}>
              <span className="bar-label">{severity}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(count / maxSeverityCount) * 100}%` }} />
              </div>
              <span className="bar-count">{count}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
