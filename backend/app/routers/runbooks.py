import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RunBook
from app.schemas.incident_schemas import (
    RunBookCreateRequest,
    RunBookResponse,
    RunBookUpdateRequest,
)

router = APIRouter(prefix="/runbooks", tags=["runbooks"])


@router.get("", response_model=list[RunBookResponse])
def list_runbooks(team: str | None = None, db: Session = Depends(get_db)):
    query = db.query(RunBook)
    if team:
        query = query.filter(RunBook.team_name == team)
    return query.all()


@router.post("", response_model=RunBookResponse, status_code=201)
def create_runbook(payload: RunBookCreateRequest, db: Session = Depends(get_db)):
    runbook = RunBook(
        team_name=payload.team_name,
        metric_pattern=payload.metric_pattern,
        title=payload.title,
        url=payload.url,
        steps=payload.steps,
    )
    db.add(runbook)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Runbook for this team + metric pattern already exists",
        )
    db.refresh(runbook)
    return runbook


@router.patch("/{runbook_id}", response_model=RunBookResponse)
def update_runbook(
    runbook_id: uuid.UUID,
    payload: RunBookUpdateRequest,
    db: Session = Depends(get_db),
):
    runbook = db.query(RunBook).filter(RunBook.id == runbook_id).first()
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(runbook, field, value)

    db.commit()
    db.refresh(runbook)
    return runbook
