import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Incident, IncidentStatus
from app.routers import alerts, escalation, incidents, runbooks
from app.services.incident_service import check_and_escalate_overdue_incidents

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_escalation_check() -> None:
    db = SessionLocal()
    try:
        check_and_escalate_overdue_incidents(db)
    except Exception:
        logger.exception("Escalation check job failed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        _run_escalation_check,
        "interval",
        seconds=settings.ESCALATION_CHECK_INTERVAL_SECONDS,
        id="escalation_check",
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Incident Response Automation", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(alerts.router)
app.include_router(escalation.router)
app.include_router(runbooks.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(Incident.id)).scalar()
    open_count = (
        db.query(func.count(Incident.id))
        .filter(Incident.status != IncidentStatus.RESOLVED)
        .scalar()
    )

    by_status = dict(
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    by_severity = dict(
        db.query(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )

    avg_mttr = (
        db.query(
            func.avg(
                func.extract("epoch", Incident.resolved_at - Incident.created_at) / 60
            )
        )
        .filter(Incident.status == IncidentStatus.RESOLVED)
        .scalar()
    )

    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "by_status": {
            status.value if hasattr(status, "value") else status: count
            for status, count in by_status.items()
        },
        "by_severity": {
            sev.value if hasattr(sev, "value") else sev: count
            for sev, count in by_severity.items()
        },
        "avg_mttr_minutes": round(avg_mttr, 2) if avg_mttr is not None else None,
    }
