from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Incident, IncidentStatus
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


@router.post("/ingest", response_model=AlertIngestResponse, status_code=201)
def ingest_alert(payload: AlertIngestRequest, db: Session = Depends(get_db)):
    existing_incident = (
        db.query(Incident)
        .join(Alert, Alert.incident_id == Incident.id)
        .filter(
            Alert.metric_name == payload.metric_name,
            Incident.status != IncidentStatus.RESOLVED,
        )
        .first()
    )

    created_new_incident = existing_incident is None

    if existing_incident:
        incident = existing_incident
        incident.alert_count += 1
        db.commit()
        db.refresh(incident)
    else:
        severity = incident_service.determine_severity_from_threshold(
            payload.threshold, payload.current_value
        )
        team = route_alert_to_team(payload.metric_name, severity)
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
