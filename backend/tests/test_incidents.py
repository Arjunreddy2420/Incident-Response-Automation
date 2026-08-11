def test_create_incident(client):
    response = client.post(
        "/incidents",
        json={
            "title": "Database down",
            "description": "RDS unreachable",
            "severity": "CRITICAL",
            "team": "data-platform",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert "created_at" in body


def test_get_incidents_list(client):
    client.post(
        "/incidents",
        json={"title": "Slow API", "severity": "HIGH", "team": "api-platform"},
    )

    response = client.get("/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) == 1
    assert incidents[0]["title"] == "Slow API"
    assert incidents[0]["mttr_minutes"] is None


def test_get_incident_detail_404(client):
    response = client.get("/incidents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_acknowledge_and_resolve_incident(client):
    create_response = client.post(
        "/incidents",
        json={"title": "Payment failures", "severity": "CRITICAL", "team": "payment-platform"},
    )
    incident_id = create_response.json()["id"]

    ack_response = client.post(
        f"/incidents/{incident_id}/acknowledge",
        json={"engineer_name": "arjun"},
    )
    assert ack_response.status_code == 200
    assert ack_response.json()["status"] == "ACKNOWLEDGED"
    assert ack_response.json()["assigned_engineer"] == "arjun"

    resolve_response = client.post(
        f"/incidents/{incident_id}/resolve",
        json={"resolution_summary": "Restarted RDS connection pool"},
    )
    assert resolve_response.status_code == 200
    resolved_body = resolve_response.json()
    assert resolved_body["status"] == "RESOLVED"
    assert resolved_body["resolved_at"] is not None
    assert resolved_body["mttr_minutes"] is not None
    assert resolved_body["mttr_minutes"] >= 0


def test_resolve_already_resolved_incident_fails(client):
    create_response = client.post(
        "/incidents",
        json={"title": "Flaky test", "severity": "LOW", "team": "on-call-general"},
    )
    incident_id = create_response.json()["id"]

    client.post(f"/incidents/{incident_id}/resolve", json={"resolution_summary": "fixed"})
    second_resolve = client.post(f"/incidents/{incident_id}/resolve", json={"resolution_summary": "fixed again"})
    assert second_resolve.status_code == 400
