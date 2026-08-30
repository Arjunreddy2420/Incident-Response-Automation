from app.models import Alert, IncidentSeverity, RunBook
from app.services.incident_service import create_incident, get_incident_detail
from app.services.runbook_service import find_runbook_for_incident


def test_list_runbooks_filtered_by_team(client):
    response = client.get("/runbooks", params={"team": "payment-platform"})
    assert response.status_code == 200
    runbooks = response.json()
    assert len(runbooks) >= 1
    assert all(rb["team_name"] == "payment-platform" for rb in runbooks)


def test_create_and_update_runbook(client, db_session):
    created = client.post(
        "/runbooks",
        json={
            "team_name": "networking",
            "metric_pattern": "packet_loss",
            "title": "Network Packet Loss Runbook",
            "url": "https://runbooks.internal/network-packet-loss",
            "steps": ["Check switch health", "Check BGP session status"],
        },
    )
    try:
        assert created.status_code == 201
        body = created.json()
        assert body["team_name"] == "networking"
        assert body["steps"] == ["Check switch health", "Check BGP session status"]

        updated = client.patch(
            f"/runbooks/{body['id']}",
            json={"title": "Updated Network Runbook"},
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Updated Network Runbook"
    finally:
        db_session.query(RunBook).filter(RunBook.team_name == "networking").delete()
        db_session.commit()


def test_incident_runbook_endpoint_matches_by_metric_pattern(client, db_session):
    incident = create_incident(
        db_session,
        title="Auth login failures spiking",
        description=None,
        severity=IncidentSeverity.HIGH,
        team="auth",
        engineer="carol",
    )
    db_session.add(
        Alert(incident_id=incident.id, source="prometheus", metric_name="auth_login_failures")
    )
    db_session.commit()

    response = client.get(f"/incidents/{incident.id}/runbook")
    assert response.status_code == 200
    assert response.json()["team_name"] == "auth"


def test_incident_runbook_endpoint_404_when_no_team(client, db_session):
    incident = create_incident(
        db_session,
        title="Unrouted issue",
        description=None,
        severity=IncidentSeverity.LOW,
        team=None,
        engineer=None,
    )
    response = client.get(f"/incidents/{incident.id}/runbook")
    assert response.status_code == 404


def test_find_runbook_falls_back_to_generic_for_team(db_session):
    incident = create_incident(
        db_session,
        title="Something odd",
        description=None,
        severity=IncidentSeverity.LOW,
        team="on-call-general",
        engineer="grace",
    )
    db_session.add(
        Alert(incident_id=incident.id, source="prometheus", metric_name="mystery_metric")
    )
    db_session.commit()

    incident = get_incident_detail(db_session, incident.id)
    runbook = find_runbook_for_incident(db_session, incident)

    assert runbook is not None
    assert runbook.team_name == "on-call-general"
    assert runbook.metric_pattern is None
