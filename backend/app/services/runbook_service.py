from sqlalchemy.orm import Session

from app.models import Incident, RunBook


def find_runbook_for_incident(db: Session, incident: Incident) -> RunBook | None:
    if not incident.assigned_team:
        return None

    team_runbooks = (
        db.query(RunBook).filter(RunBook.team_name == incident.assigned_team).all()
    )
    if not team_runbooks:
        return None

    metric_names = [alert.metric_name.lower() for alert in incident.alerts]

    for runbook in team_runbooks:
        if not runbook.metric_pattern:
            continue
        pattern = runbook.metric_pattern.lower()
        if any(pattern in metric_name for metric_name in metric_names):
            return runbook

    generic = next((rb for rb in team_runbooks if not rb.metric_pattern), None)
    return generic or team_runbooks[0]
