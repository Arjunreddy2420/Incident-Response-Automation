import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import IncidentSeverity, IncidentStatus

# ---- Alerts ----


class AlertIngestRequest(BaseModel):
    source: str  # prometheus, datadog, pagerduty
    metric_name: str
    threshold: float | None = None
    current_value: float | None = None
    alert_message: str | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    source: str
    metric_name: str
    threshold: float | None
    current_value: float | None
    alert_message: str | None
    received_at: datetime


class AlertIngestResponse(BaseModel):
    incident_id: uuid.UUID
    alert_id: uuid.UUID
    created_new_incident: bool
    assigned_team: str
    assigned_engineer: str | None


# ---- Timeline ----


class IncidentTimelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    event_type: str
    actor: str | None
    message: str | None
    timestamp: datetime


# ---- Incidents ----


class IncidentCreateRequest(BaseModel):
    title: str
    description: str | None = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    team: str


class IncidentCreateResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime


class IncidentUpdateRequest(BaseModel):
    status: IncidentStatus | None = None
    assigned_engineer: str | None = None
    tags: list[str] | None = None


class IncidentAcknowledgeRequest(BaseModel):
    engineer_name: str


class IncidentResolveRequest(BaseModel):
    resolution_summary: str | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: IncidentStatus
    severity: IncidentSeverity
    assigned_team: str | None
    assigned_engineer: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    alert_count: int
    mttr_minutes: int | None
    tags: list[str] | None


class IncidentDetailResponse(IncidentResponse):
    alerts: list[AlertResponse] = []
    timeline: list[IncidentTimelineResponse] = []


# ---- Escalation Policies ----


class EscalationPolicyCreateRequest(BaseModel):
    team_name: str
    severity: IncidentSeverity
    on_call_engineer: str
    backup_engineer: str | None = None
    escalation_time_minutes: int = 30
    slack_channel: str | None = None


class EscalationPolicyUpdateRequest(BaseModel):
    on_call_engineer: str | None = None
    backup_engineer: str | None = None
    escalation_time_minutes: int | None = None
    slack_channel: str | None = None


class EscalationPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_name: str
    severity_level: IncidentSeverity
    on_call_engineer: str
    backup_engineer: str | None
    escalation_time_minutes: int
    slack_channel: str | None


# ---- RunBooks ----


class RunBookCreateRequest(BaseModel):
    team_name: str
    metric_pattern: str | None = None
    title: str
    url: str
    steps: list[str] | None = None


class RunBookUpdateRequest(BaseModel):
    metric_pattern: str | None = None
    title: str | None = None
    url: str | None = None
    steps: list[str] | None = None


class RunBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_name: str
    metric_pattern: str | None
    title: str
    url: str
    steps: list[str] | None
    created_at: datetime
    updated_at: datetime
