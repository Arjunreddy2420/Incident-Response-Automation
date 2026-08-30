import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"  # P1
    HIGH = "HIGH"  # P2
    MEDIUM = "MEDIUM"  # P3
    LOW = "LOW"  # P4


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status"),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity"),
        default=IncidentSeverity.MEDIUM,
        nullable=False,
    )
    assigned_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_engineer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    alert_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)

    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    timeline: Mapped[list["IncidentTimeline"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )

    @property
    def mttr_minutes(self) -> int | None:
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.created_at
        return int(delta.total_seconds() // 60)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # prometheus, datadog, pagerduty
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship(back_populates="alerts")


class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity_level: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity"), nullable=False
    )
    on_call_engineer: Mapped[str] = mapped_column(String(100), nullable=False)
    backup_engineer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    escalation_time_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    slack_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)


class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # created, acknowledged, escalated, resolved
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship(back_populates="timeline")


class RunBook(Base):
    __tablename__ = "runbooks"
    __table_args__ = (UniqueConstraint("team_name", "metric_pattern"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    steps: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
