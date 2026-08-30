import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IncidentSeverity, IncidentStatus
from app.schemas.incident_schemas import (
    IncidentAcknowledgeRequest,
    IncidentCreateRequest,
    IncidentCreateResponse,
    IncidentDetailResponse,
    IncidentResolveRequest,
    IncidentResponse,
    IncidentUpdateRequest,
    RunBookResponse,
)
from app.services import incident_service
from app.services.routing_service import get_slack_channel_for_team
from app.services.runbook_service import find_runbook_for_incident
from app.services.slack_service import (
    format_incident_created_message,
    format_incident_resolved_message,
    send_slack_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _get_incident_or_404(db: Session, incident_id: uuid.UUID):
    incident = incident_service.get_incident_detail(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentCreateResponse, status_code=201)
def create_incident(payload: IncidentCreateRequest, db: Session = Depends(get_db)):
    incident = incident_service.create_incident(
        db, payload.title, payload.description, payload.severity, payload.team
    )

    channel = get_slack_channel_for_team(db, incident.assigned_team, incident.severity)
    send_slack_notification(channel, format_incident_created_message(incident))

    return IncidentCreateResponse(id=incident.id, created_at=incident.created_at)


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    team: str | None = None,
    db: Session = Depends(get_db),
):
    return incident_service.get_incidents(
        db, status=status, severity=severity, team=team
    )


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_incident_or_404(db, incident_id)


@router.get("/{incident_id}/runbook", response_model=RunBookResponse)
def get_incident_runbook(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    incident = _get_incident_or_404(db, incident_id)
    runbook = find_runbook_for_incident(db, incident)
    if not runbook:
        raise HTTPException(
            status_code=404, detail="No runbook linked to this incident"
        )
    return runbook


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdateRequest,
    db: Session = Depends(get_db),
):
    incident = _get_incident_or_404(db, incident_id)
    return incident_service.update_incident(
        db,
        incident,
        status=payload.status,
        assigned_engineer=payload.assigned_engineer,
        tags=payload.tags,
    )


@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(
    incident_id: uuid.UUID,
    payload: IncidentAcknowledgeRequest,
    db: Session = Depends(get_db),
):
    incident = _get_incident_or_404(db, incident_id)
    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(
            status_code=400, detail="Cannot acknowledge a resolved incident"
        )

    incident = incident_service.acknowledge_incident(
        db, incident, payload.engineer_name
    )

    channel = get_slack_channel_for_team(db, incident.assigned_team, incident.severity)
    send_slack_notification(
        channel, f"Incident acknowledged by @{payload.engineer_name}"
    )

    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: uuid.UUID,
    payload: IncidentResolveRequest,
    db: Session = Depends(get_db),
):
    incident = _get_incident_or_404(db, incident_id)
    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Incident already resolved")

    incident = incident_service.resolve_incident(
        db, incident, payload.resolution_summary
    )

    channel = get_slack_channel_for_team(db, incident.assigned_team, incident.severity)
    mttr = incident_service.calculate_mttr(incident) or 0
    send_slack_notification(channel, format_incident_resolved_message(incident, mttr))

    return incident
