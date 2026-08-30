from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import (
    Alert,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimeline,
)
from app.schemas.incident_schemas import AlertIngestRequest, AlertIngestResponse
from app.services import incident_service
from app.services.routing_service import (
    get_on_call_engineer,
    get_slack_channel_for_team,
    route_alert_to_team,
)
from app.services.slack_service import (
    format_incident_created_message,
    send_slack_notification,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Escalate severity one tier for every this-many additional alerts on the same incident.
RATE_ESCALATION_ALERT_INTERVAL = 3


@router.post("/ingest", response_model=AlertIngestResponse, status_code=201)
def ingest_alert(payload: AlertIngestRequest, db: Session = Depends(get_db)):
    # Team routing doesn't depend on severity (see route_alert_to_team), so this is
    # safe to compute before severity is known — needed either way for correlation.
    team = route_alert_to_team(payload.metric_name, IncidentSeverity.MEDIUM)

    existing_incident = (
        db.query(Incident)
        .join(Alert, Alert.incident_id == Incident.id)
        .filter(
            Alert.metric_name == payload.metric_name,
            Incident.status != IncidentStatus.RESOLVED,
        )
        .first()
    )

    correlated = False
    if existing_incident is None:
        # No exact metric match — fall back to correlating by team + recency, so
        # related alerts (e.g. "db_connections" and "db_latency") group into one
        # incident instead of each spawning its own.
        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.ALERT_CORRELATION_WINDOW_MINUTES
        )
        existing_incident = (
            db.query(Incident)
            .filter(
                Incident.assigned_team == team,
                Incident.status != IncidentStatus.RESOLVED,
                Incident.created_at >= window_start,
            )
            .order_by(Incident.created_at.desc())
            .first()
        )
        correlated = existing_incident is not None

    created_new_incident = existing_incident is None

    if existing_incident:
        incident = existing_incident
        incident.alert_count += 1

        if correlated:
            db.add(
                IncidentTimeline(
                    incident_id=incident.id,
                    event_type="correlated",
                    actor="system",
                    message=(
                        f"Correlated alert from {payload.source} "
                        f"({payload.metric_name}) grouped into this incident"
                    ),
                )
            )

        if (
            incident.alert_count % RATE_ESCALATION_ALERT_INTERVAL == 0
            and incident.severity != IncidentSeverity.CRITICAL
        ):
            previous_severity = incident.severity
            incident.severity = incident_service.escalate_severity_one_tier(
                incident.severity
            )
            db.add(
                IncidentTimeline(
                    incident_id=incident.id,
                    event_type="escalated",
                    actor="system",
                    message=(
                        f"Severity escalated {previous_severity.value} -> "
                        f"{incident.severity.value} after {incident.alert_count} "
                        "repeated alerts"
                    ),
                )
            )
            channel = get_slack_channel_for_team(
                db, incident.assigned_team, incident.severity
            )
            send_slack_notification(
                channel,
                f"⬆️ Incident '{incident.title}' escalated to "
                f"{incident.severity.value} after {incident.alert_count} "
                "repeated alerts",
            )

        db.commit()
        db.refresh(incident)
    else:
        severity = incident_service.determine_severity_from_threshold(
            payload.threshold, payload.current_value, team=team, recent_alert_count=1
        )
        engineer = get_on_call_engineer(db, team, severity)

        incident = incident_service.create_incident(
            db,
            title=f"{payload.metric_name} threshold breached",
            description=payload.alert_message,
            severity=severity,
            team=team,
            engineer=engineer,
        )
        incident.alert_count = 1
        db.commit()
        db.refresh(incident)

        channel = get_slack_channel_for_team(db, team, severity)
        send_slack_notification(channel, format_incident_created_message(incident))

    alert = Alert(
        incident_id=incident.id,
        source=payload.source,
        metric_name=payload.metric_name,
        threshold=payload.threshold,
        current_value=payload.current_value,
        alert_message=payload.alert_message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return AlertIngestResponse(
        incident_id=incident.id,
        alert_id=alert.id,
        created_new_incident=created_new_incident,
        assigned_team=incident.assigned_team,
        assigned_engineer=incident.assigned_engineer,
    )
