# Incident Response Automation

Automated incident ingestion and routing platform that reduces manual triage time by turning
raw monitoring alerts (Prometheus, Datadog, PagerDuty) into routed, tracked incidents with
Slack notifications and MTTR reporting.

## Phase 1 (current): Foundation

- FastAPI backend backed by PostgreSQL
- Alert ingestion with automatic team routing and on-call assignment
- Incident lifecycle: create → acknowledge → resolve, with a full timeline
- Slack notifications on incident creation and resolution
- Docker Compose for local development, GitHub Actions for CI

Kubernetes manifests, Terraform IaC, and a frontend UI are planned for later phases.

## Project layout

```
backend/app/
  main.py            FastAPI app, health + metrics endpoints
  models.py           SQLAlchemy ORM models (Incident, Alert, EscalationPolicy, IncidentTimeline)
  database.py          Engine/session setup
  config.py             Environment-driven settings
  routers/                incidents, alerts, escalation endpoints
  services/                 business logic (incident, routing, Slack)
  schemas/                    Pydantic request/response models
database/               schema.sql + init.sql (seed data)
```

## Local development

1. Copy the example env file and fill in your Slack webhook (optional locally):
   ```
   cp .env.example .env
   ```
2. Start Postgres + API:
   ```
   docker-compose up --build
   ```
3. API is available at http://localhost:8000, health check at `GET /health`.

Postgres is initialized automatically from `database/schema.sql` and `database/init.sql`
on first container start (via `docker-entrypoint-initdb.d`).

## Running tests

Tests run against a real PostgreSQL instance (matching CI). With `docker-compose up`
running, or any Postgres reachable via `DATABASE_URL`:

```
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## API examples

Create an incident:
```
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"title": "Database down", "description": "RDS unreachable", "severity": "CRITICAL", "team": "data-platform"}'
```

List incidents:
```
curl http://localhost:8000/incidents
```

Ingest an alert (auto-creates or attaches to an existing open incident, routes to a team,
and assigns the on-call engineer):
```
curl -X POST http://localhost:8000/alerts/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "prometheus", "metric_name": "db_connections", "threshold": 100, "current_value": 450}'
```

Acknowledge an incident:
```
curl -X POST http://localhost:8000/incidents/{id}/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"engineer_name": "arjun"}'
```

Resolve an incident:
```
curl -X POST http://localhost:8000/incidents/{id}/resolve \
  -H "Content-Type: application/json" \
  -d '{"resolution_summary": "Restarted RDS connection pool"}'
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://incidents_user:incidents_password@localhost:5432/incidents` |
| `SLACK_WEBHOOK_URL` | Incoming webhook for Slack notifications | unset (notifications are skipped and logged) |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `PORT` | API port | `8000` |

`SLACK_WEBHOOK_URL` should never be committed — set it locally in `.env` (gitignored) or as a
GitHub Actions secret in CI/CD.
