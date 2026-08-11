-- Incident Response Automation Platform - PostgreSQL schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED')),
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    assigned_team VARCHAR(100),
    assigned_engineer VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    alert_count INT NOT NULL DEFAULT 0,
    tags TEXT[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents (severity);
CREATE INDEX IF NOT EXISTS idx_incidents_team ON incidents (assigned_team);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents (created_at);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    threshold FLOAT,
    current_value FLOAT,
    alert_message TEXT,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_incident ON alerts (incident_id);
CREATE INDEX IF NOT EXISTS idx_alerts_metric_name ON alerts (metric_name);

CREATE TABLE IF NOT EXISTS escalation_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name VARCHAR(100) NOT NULL,
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    on_call_engineer VARCHAR(100) NOT NULL,
    backup_engineer VARCHAR(100),
    escalation_time_minutes INT NOT NULL DEFAULT 30,
    slack_channel VARCHAR(100),
    UNIQUE (team_name, severity_level)
);

CREATE TABLE IF NOT EXISTS incident_timeline (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    actor VARCHAR(100),
    message TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_timeline_incident ON incident_timeline (incident_id);

-- Keep updated_at current on every row change.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_incidents_updated_at ON incidents;
CREATE TRIGGER trg_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- Recomputes alert_count and returns MTTR (minutes) for a given incident.
CREATE OR REPLACE FUNCTION calculate_incident_metrics(p_incident_id UUID)
RETURNS TABLE (alert_count INT, mttr_minutes INT) AS $$
DECLARE
    v_alert_count INT;
    v_mttr_minutes INT;
BEGIN
    SELECT COUNT(*) INTO v_alert_count FROM alerts WHERE incident_id = p_incident_id;

    SELECT
        CASE
            WHEN i.resolved_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 60
            ELSE NULL
        END
    INTO v_mttr_minutes
    FROM incidents i
    WHERE i.id = p_incident_id;

    UPDATE incidents SET alert_count = v_alert_count WHERE id = p_incident_id;

    RETURN QUERY SELECT v_alert_count, v_mttr_minutes;
END;
$$ LANGUAGE plpgsql;
