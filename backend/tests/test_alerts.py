def test_correlated_alerts_group_into_one_incident(client):
    first = client.post(
        "/alerts/ingest",
        json={
            "source": "prometheus",
            "metric_name": "payment_gateway_errors",
            "threshold": 100,
            "current_value": 120,
        },
    )
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["created_new_incident"] is True
    assert first_body["assigned_team"] == "payment-platform"

    # Different metric_name, same team, within the correlation window -> should
    # group into the same incident instead of spawning a new one.
    second = client.post(
        "/alerts/ingest",
        json={
            "source": "datadog",
            "metric_name": "payment_latency_spike",
            "threshold": 100,
            "current_value": 130,
        },
    )
    assert second.status_code == 201
    second_body = second.json()
    assert second_body["created_new_incident"] is False
    assert second_body["incident_id"] == first_body["incident_id"]

    incident = client.get(f"/incidents/{first_body['incident_id']}").json()
    assert incident["alert_count"] == 2
    assert any(entry["event_type"] == "correlated" for entry in incident["timeline"])


def test_repeated_alerts_escalate_severity(client):
    payload = {
        "source": "prometheus",
        "metric_name": "checkout_latency",
        "threshold": 100,
        "current_value": 120,
    }
    first = client.post("/alerts/ingest", json=payload)
    incident_id = first.json()["incident_id"]
    initial = client.get(f"/incidents/{incident_id}").json()
    assert initial["severity"] == "MEDIUM"

    client.post("/alerts/ingest", json=payload)
    third = client.post("/alerts/ingest", json=payload)
    assert third.json()["incident_id"] == incident_id

    escalated = client.get(f"/incidents/{incident_id}").json()
    assert escalated["alert_count"] == 3
    assert escalated["severity"] == "HIGH"
    assert any(entry["event_type"] == "escalated" for entry in escalated["timeline"])
