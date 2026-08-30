from sqlalchemy import text

from app.models import IncidentSeverity, IncidentStatus
from app.services.incident_service import (
    check_and_escalate_overdue_incidents,
    create_incident,
)


def _backdate(db_session, incident_id, minutes):
    db_session.execute(
        text(
            "UPDATE incidents SET created_at = created_at - make_interval(mins => :minutes) "
            "WHERE id = :id"
        ),
        {"minutes": minutes, "id": incident_id},
    )
    db_session.commit()


def test_overdue_incident_is_escalated_to_backup_engineer(db_session):
    incident = create_incident(
        db_session,
        title="Payment gateway down",
        description=None,
        severity=IncidentSeverity.CRITICAL,
        team="payment-platform",
        engineer="alice",
    )
    # payment-platform/CRITICAL escalation_time_minutes is 15 (seeded).
    _backdate(db_session, incident.id, minutes=20)

    escalated = check_and_escalate_overdue_incidents(db_session)

    assert len(escalated) == 1
    assert escalated[0].id == incident.id
    assert escalated[0].assigned_engineer == "bob"
    assert escalated[0].escalated_at is not None

    db_session.refresh(incident)
    timeline_events = [entry.event_type for entry in incident.timeline]
    assert "escalated" in timeline_events


def test_fresh_incident_is_not_escalated(db_session):
    incident = create_incident(
        db_session,
        title="Payment gateway blip",
        description=None,
        severity=IncidentSeverity.CRITICAL,
        team="payment-platform",
        engineer="alice",
    )

    escalated = check_and_escalate_overdue_incidents(db_session)

    assert incident.id not in [i.id for i in escalated]


def test_already_escalated_incident_is_not_escalated_twice(db_session):
    incident = create_incident(
        db_session,
        title="Payment gateway down again",
        description=None,
        severity=IncidentSeverity.CRITICAL,
        team="payment-platform",
        engineer="alice",
    )
    _backdate(db_session, incident.id, minutes=20)

    first_pass = check_and_escalate_overdue_incidents(db_session)
    second_pass = check_and_escalate_overdue_incidents(db_session)

    assert incident.id in [i.id for i in first_pass]
    assert incident.id not in [i.id for i in second_pass]


def test_incident_without_matching_policy_is_skipped(db_session):
    incident = create_incident(
        db_session,
        title="Unrouted issue",
        description=None,
        severity=IncidentSeverity.CRITICAL,
        team="nonexistent-team",
        engineer=None,
    )
    _backdate(db_session, incident.id, minutes=60)

    escalated = check_and_escalate_overdue_incidents(db_session)

    assert incident.id not in [i.id for i in escalated]
    assert incident.status == IncidentStatus.OPEN
