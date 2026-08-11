from sqlalchemy.orm import Session

from app.models import EscalationPolicy, IncidentSeverity

# Ordered mapping of metric_name substrings to owning team.
METRIC_TEAM_ROUTES: list[tuple[str, str]] = [
    ("payment", "payment-platform"),
    ("auth", "auth"),
    ("checkout", "checkout"),
    ("db", "data-platform"),
    ("database", "data-platform"),
    ("network", "networking"),
    ("api", "api-platform"),
]

DEFAULT_TEAM = "on-call-general"


def route_alert_to_team(metric_name: str, severity: IncidentSeverity) -> str:
    metric_lower = metric_name.lower()
    for keyword, team in METRIC_TEAM_ROUTES:
        if keyword in metric_lower:
            return team
    return DEFAULT_TEAM


def get_on_call_engineer(
    db: Session, team_name: str, severity: IncidentSeverity
) -> str | None:
    policy = (
        db.query(EscalationPolicy)
        .filter(
            EscalationPolicy.team_name == team_name,
            EscalationPolicy.severity_level == severity,
        )
        .first()
    )
    return policy.on_call_engineer if policy else None


def get_slack_channel_for_team(
    db: Session, team_name: str | None, severity: IncidentSeverity
) -> str | None:
    if not team_name:
        return None
    policy = (
        db.query(EscalationPolicy)
        .filter(
            EscalationPolicy.team_name == team_name,
            EscalationPolicy.severity_level == severity,
        )
        .first()
    )
    return policy.slack_channel if policy else None
