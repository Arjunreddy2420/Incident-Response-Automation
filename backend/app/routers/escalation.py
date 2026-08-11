import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EscalationPolicy
from app.schemas.incident_schemas import (
    EscalationPolicyCreateRequest,
    EscalationPolicyResponse,
    EscalationPolicyUpdateRequest,
)

router = APIRouter(prefix="/escalation-policies", tags=["escalation"])


@router.get("", response_model=list[EscalationPolicyResponse])
def list_escalation_policies(db: Session = Depends(get_db)):
    return db.query(EscalationPolicy).all()


@router.post("", response_model=EscalationPolicyResponse, status_code=201)
def create_escalation_policy(
    payload: EscalationPolicyCreateRequest, db: Session = Depends(get_db)
):
    policy = EscalationPolicy(
        team_name=payload.team_name,
        severity_level=payload.severity,
        on_call_engineer=payload.on_call_engineer,
        backup_engineer=payload.backup_engineer,
        escalation_time_minutes=payload.escalation_time_minutes,
        slack_channel=payload.slack_channel,
    )
    db.add(policy)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Escalation policy for this team + severity already exists",
        )
    db.refresh(policy)
    return policy


@router.patch("/{policy_id}", response_model=EscalationPolicyResponse)
def update_escalation_policy(
    policy_id: uuid.UUID,
    payload: EscalationPolicyUpdateRequest,
    db: Session = Depends(get_db),
):
    policy = db.query(EscalationPolicy).filter(EscalationPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)
    return policy
