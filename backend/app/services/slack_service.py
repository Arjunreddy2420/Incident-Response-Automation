import logging

import httpx

from app.config import settings
from app.models import Incident

logger = logging.getLogger(__name__)

DASHBOARD_BASE_URL = "https://dashboard.internal/incidents"


def send_slack_notification(
    channel: str | None, message: str, blocks: list[dict] | None = None
) -> bool:
    if not settings.SLACK_WEBHOOK_URL:
        logger.info(
            "SLACK_WEBHOOK_URL not configured, skipping notification: %s", message
        )
        return False

    payload: dict = {"text": message}
    if channel:
        payload["channel"] = channel
    if blocks:
        payload["blocks"] = blocks

    try:
        response = httpx.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Failed to send Slack notification")
        return False


def format_incident_created_message(incident: Incident) -> str:
    return (
        f"🚨 NEW INCIDENT: {incident.title} [{incident.severity.value}]\n"
        f"Description: {incident.description or 'N/A'}\n"
        f"Team: {incident.assigned_team or 'unassigned'}\n"
        f"Dashboard: {DASHBOARD_BASE_URL}/{incident.id}"
    )


def format_incident_resolved_message(incident: Incident, mttr_minutes: int) -> str:
    return (
        f"✅ INCIDENT RESOLVED: {incident.title}\n"
        f"MTTR: {mttr_minutes} minutes\n"
        f"Dashboard: {DASHBOARD_BASE_URL}/{incident.id}"
    )
