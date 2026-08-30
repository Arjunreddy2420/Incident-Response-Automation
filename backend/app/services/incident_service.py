import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models import Incident, IncidentSeverity, IncidentStatus, IncidentTimeline
from app.services.routing_service import (
    get_escalation_policy,
    get_slack_channel_for_team,
)
from app.services.slack_service import send_slack_notification


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


#  Deterministic, explainable severity scoring (no ML model — see project notes on
#  why: there's no historical incident data yet to train one on). Score of 1-4 maps
#  to LOW-CRITICAL; threshold ratio sets the base, then repeated-alert frequency and
#  team business-criticality can each raise it by a tier.
_SEVERITY_BY_SCORE = {
    4: IncidentSeverity.CRITICAL,
    3: IncidentSeverity.HIGH,
    2: IncidentSeverity.MEDIUM,
    1: IncidentSeverity.LOW,
}
_SEVERITY_ORDER = [
    IncidentSeverity.LOW,
    IncidentSeverity.MEDIUM,
    IncidentSeverity.HIGH,
    IncidentSeverity.CRITICAL,
]
# Teams whose incidents carry outsized business impact regardless of raw metrics.
CRITICAL_TEAMS = {"payment-platform", "auth"}
# Repeated alerts for the same problem raise confidence it's real, not noise.
FREQUENCY_ESCALATION_THRESHOLD = 5


def determine_severity_from_threshold(
    threshold: float | None,
    current_value: float | None,
    *,
    team: str | None = None,
    recent_alert_count: int = 1,
) -> IncidentSeverity:
    if threshold is None or current_value is None or threshold == 0:
        score = 2
    else:
        ratio = current_value / threshold
        if ratio >= 3:
            score = 4
        elif ratio >= 2:
            score = 3
        elif ratio >= 1:
            score = 2
        else:
            score = 1

    if recent_alert_count >= FREQUENCY_ESCALATION_THRESHOLD:
        score += 1

    # Don't let team weighting turn a clearly-LOW signal into something noisier.
    if team in CRITICAL_TEAMS and score >= 2:
        score += 1

    score = max(1, min(4, score))
    return _SEVERITY_BY_SCORE[score]


def escalate_severity_one_tier(severity: IncidentSeverity) -> IncidentSeverity:
    index = _SEVERITY_ORDER.index(severity)
    return _SEVERITY_ORDER[min(index + 1, len(_SEVERITY_ORDER) - 1)]


def check_and_escalate_overdue_incidents(db: Session) -> list[Incident]:
    """Reassign to the backup engineer any OPEN incident that has sat unacknowledged
    past its team/severity escalation window. Called on a timer from main.py, but kept
    as a plain function here so it's testable without running the scheduler."""
    now = datetime.now(timezone.utc)
    candidates = (
        db.query(Incident)
        .filter(Incident.status == IncidentStatus.OPEN, Incident.escalated_at.is_(None))
        .all()
    )

    escalated = []
    for incident in candidates:
        if not incident.assigned_team:
            continue
        policy = get_escalation_policy(db, incident.assigned_team, incident.severity)
        if not policy:
            continue

        created_at = incident.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_minutes = (now - created_at).total_seconds() / 60
        if age_minutes < policy.escalation_time_minutes:
            continue

        incident.escalated_at = now
        if policy.backup_engineer:
            incident.assigned_engineer = policy.backup_engineer
        db.add(
            IncidentTimeline(
                incident_id=incident.id,
                event_type="escalated",
                actor="system",
                message=(
                    f"Auto-escalated to backup engineer "
                    f"{policy.backup_engineer or '(none configured)'} after "
                    f"{policy.escalation_time_minutes} minutes without acknowledgment"
                ),
            )
        )
        escalated.append(incident)

    if escalated:
        db.commit()
        for incident in escalated:
            db.refresh(incident)
            channel = get_slack_channel_for_team(
                db, incident.assigned_team, incident.severity
            )
            send_slack_notification(
                channel,
                f"⚠️ Incident '{incident.title}' auto-escalated to "
                f"{incident.assigned_engineer or 'backup engineer'} after no "
                "acknowledgment within the escalation window",
            )

    return escalated
