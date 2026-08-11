import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models import Incident, IncidentSeverity, IncidentStatus, IncidentTimeline


def create_incident(
    db: Session,
    title: str,
    description: str | None,
    severity: IncidentSeverity,
    team: str,
    engineer: str | None = None,
) -> Incident:
    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        assigned_team=team,
        assigned_engineer=engineer,
    )
    db.add(incident)
    db.flush()

    db.add(
        IncidentTimeline(
            incident_id=incident.id,
            event_type="created",
            actor=engineer,
            message=f"Incident created with severity {severity.value}",
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


def get_incidents(
    db: Session,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    team: str | None = None,
) -> list[Incident]:
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if team:
        query = query.filter(Incident.assigned_team == team)
    return query.order_by(Incident.created_at.desc()).all()


def get_incident_detail(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return (
        db.query(Incident)
        .options(selectinload(Incident.alerts), selectinload(Incident.timeline))
        .filter(Incident.id == incident_id)
        .first()
    )


def update_incident(
    db: Session,
    incident: Incident,
    status: IncidentStatus | None = None,
    assigned_engineer: str | None = None,
    tags: list[str] | None = None,
) -> Incident:
    changes = []
    if status is not None and status != incident.status:
        incident.status = status
        changes.append(f"status -> {status.value}")
    if (
        assigned_engineer is not None
        and assigned_engineer != incident.assigned_engineer
    ):
        incident.assigned_engineer = assigned_engineer
        changes.append(f"assigned_engineer -> {assigned_engineer}")
    if tags is not None:
        incident.tags = tags
        changes.append("tags updated")

    if changes:
        db.add(
            IncidentTimeline(
                incident_id=incident.id,
                event_type="updated",
                actor=assigned_engineer or incident.assigned_engineer,
                message="; ".join(changes),
            )
        )

    db.commit()
    db.refresh(incident)
    return incident


def acknowledge_incident(
    db: Session, incident: Incident, engineer_name: str
) -> Incident:
    incident.status = IncidentStatus.ACKNOWLEDGED
    incident.assigned_engineer = engineer_name
    db.add(
        IncidentTimeline(
            incident_id=incident.id,
            event_type="acknowledged",
            actor=engineer_name,
            message=f"Incident acknowledged by {engineer_name}",
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


def resolve_incident(
    db: Session, incident: Incident, resolution_summary: str | None
) -> Incident:
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.now(timezone.utc)
    db.add(
        IncidentTimeline(
            incident_id=incident.id,
            event_type="resolved",
            actor=incident.assigned_engineer,
            message=resolution_summary or "Incident resolved",
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


def calculate_mttr(incident: Incident) -> int | None:
    return incident.mttr_minutes


def determine_severity_from_threshold(
    threshold: float | None, current_value: float | None
) -> IncidentSeverity:
    if threshold is None or current_value is None or threshold == 0:
        return IncidentSeverity.MEDIUM

    ratio = current_value / threshold
    if ratio >= 3:
        return IncidentSeverity.CRITICAL
    if ratio >= 2:
        return IncidentSeverity.HIGH
    if ratio >= 1:
        return IncidentSeverity.MEDIUM
    return IncidentSeverity.LOW
