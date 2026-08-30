import pytest

from app.models import IncidentSeverity
from app.services.incident_service import (
    determine_severity_from_threshold,
    escalate_severity_one_tier,
)
from app.services.routing_service import get_on_call_engineer, route_alert_to_team


@pytest.mark.parametrize(
    "metric_name,expected_team",
    [
        ("payment_gateway_errors", "payment-platform"),
        ("auth_login_failures", "auth"),
        ("db_connections", "data-platform"),
        ("checkout_latency", "checkout"),
        ("network_packet_loss", "networking"),
        ("api_5xx_rate", "api-platform"),
        ("totally_unrelated_metric", "on-call-general"),
    ],
)
def test_route_alert_to_team(metric_name, expected_team):
    assert route_alert_to_team(metric_name, IncidentSeverity.MEDIUM) == expected_team


@pytest.mark.parametrize(
    "threshold,current_value,expected_severity",
    [
        (100, 450, IncidentSeverity.CRITICAL),
        (100, 250, IncidentSeverity.HIGH),
        (100, 120, IncidentSeverity.MEDIUM),
        (100, 50, IncidentSeverity.LOW),
        (None, None, IncidentSeverity.MEDIUM),
    ],
)
def test_determine_severity_from_threshold(threshold, current_value, expected_severity):
    assert determine_severity_from_threshold(threshold, current_value) == expected_severity


def test_severity_escalates_for_critical_team():
    # Ratio alone gives MEDIUM (score 2); payment-platform bumps it to HIGH.
    baseline = determine_severity_from_threshold(100, 120)
    weighted = determine_severity_from_threshold(100, 120, team="payment-platform")
    assert baseline == IncidentSeverity.MEDIUM
    assert weighted == IncidentSeverity.HIGH


def test_severity_team_weighting_does_not_lift_low():
    # A clearly LOW signal shouldn't get promoted just because of the team.
    assert (
        determine_severity_from_threshold(100, 50, team="payment-platform")
        == IncidentSeverity.LOW
    )


def test_severity_escalates_for_alert_frequency():
    baseline = determine_severity_from_threshold(100, 120, recent_alert_count=1)
    frequent = determine_severity_from_threshold(100, 120, recent_alert_count=5)
    assert baseline == IncidentSeverity.MEDIUM
    assert frequent == IncidentSeverity.HIGH


def test_severity_score_clamps_at_critical():
    assert (
        determine_severity_from_threshold(
            100, 450, team="payment-platform", recent_alert_count=10
        )
        == IncidentSeverity.CRITICAL
    )


@pytest.mark.parametrize(
    "severity,expected",
    [
        (IncidentSeverity.LOW, IncidentSeverity.MEDIUM),
        (IncidentSeverity.MEDIUM, IncidentSeverity.HIGH),
        (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL),
        (IncidentSeverity.CRITICAL, IncidentSeverity.CRITICAL),
    ],
)
def test_escalate_severity_one_tier(severity, expected):
    assert escalate_severity_one_tier(severity) == expected


def test_get_on_call_engineer_from_seeded_policy(db_session):
    engineer = get_on_call_engineer(db_session, "payment-platform", IncidentSeverity.CRITICAL)
    assert engineer == "alice"


def test_get_on_call_engineer_missing_policy(db_session):
    engineer = get_on_call_engineer(db_session, "nonexistent-team", IncidentSeverity.CRITICAL)
    assert engineer is None


def test_alert_ingest_creates_and_dedupes_incident(client):
    first = client.post(
        "/alerts/ingest",
        json={
            "source": "prometheus",
            "metric_name": "db_connections",
            "threshold": 100,
            "current_value": 450,
            "alert_message": "connection pool exhausted",
        },
    )
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["created_new_incident"] is True
    assert first_body["assigned_team"] == "data-platform"

    second = client.post(
        "/alerts/ingest",
        json={
            "source": "prometheus",
            "metric_name": "db_connections",
            "threshold": 100,
            "current_value": 500,
            "alert_message": "still exhausted",
        },
    )
    assert second.status_code == 201
    second_body = second.json()
    assert second_body["created_new_incident"] is False
    assert second_body["incident_id"] == first_body["incident_id"]

    incident = client.get(f"/incidents/{first_body['incident_id']}").json()
    assert incident["alert_count"] == 2
    assert len(incident["alerts"]) == 2
