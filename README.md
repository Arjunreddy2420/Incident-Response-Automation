# Incident Response Automation

[![CI/CD Pipeline](https://github.com/Arjunreddy2420/Incident-Response-Automation/actions/workflows/ci.yml/badge.svg)](https://github.com/Arjunreddy2420/Incident-Response-Automation/actions/workflows/ci.yml)

<<<<<<< Updated upstream
## Phase 1 (current): Foundation
=======
An automated incident ingestion and routing platform. It turns raw monitoring alerts
(Prometheus, Datadog, PagerDuty, or anything that can send a webhook) into routed, tracked
incidents — with automatic severity scoring, team routing, on-call assignment, Slack
notifications, correlation of related alerts, timeout-based escalation, linked runbooks, and
MTTR reporting — so nobody is manually triaging raw alert noise.
>>>>>>> Stashed changes

## Table of contents

<<<<<<< Updated upstream
Kubernetes manifests, Terraform IaC, and a frontend UI are planned for later phases.
=======
- [How it works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Design notes](#design-notes)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Infrastructure & deployment (GCP)](#infrastructure--deployment-gcp)
- [Roadmap](#roadmap)

## How it works

This system doesn't read raw application logs. Upstream monitoring tools fire a structured
alert (`source`, `metric_name`, `threshold`, `current_value`, `alert_message`) at
`POST /alerts/ingest`. From there:
>>>>>>> Stashed changes

1. **Dedup/correlate** — an exact `metric_name` match against an already-open incident wins
   first; failing that, a team + time-window fallback groups clearly-related alerts (e.g.
   `payment_latency` and `payment_errors` on the same team) into one incident instead of
   spawning a new one for every metric.
2. **Score severity** — a deterministic, explainable heuristic (not a trained ML model — see
   [Design notes](#design-notes)) combines the threshold-breach ratio, repeated-alert
   frequency, and team business-criticality into CRITICAL/HIGH/MEDIUM/LOW.
3. **Route** — the metric name is matched to an owning team, whose on-call engineer and Slack
   channel come from that team's `EscalationPolicy`.
4. **Track** — an `Incident` is created or updated with a full `IncidentTimeline` audit trail,
   and Slack is notified.
5. **Escalate** — if alerts keep repeating, severity climbs a tier. If nobody acknowledges the
   incident within its team's escalation window, a background job reassigns it to the backup
   engineer automatically.
6. **Resolve** — engineers acknowledge and resolve incidents through the API or the frontend
   dashboard, with MTTR computed automatically from the timestamps.

<<<<<<< Updated upstream
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
=======
## Features

- **Alert ingestion pipeline** — structured alert intake, dedup, correlation, severity scoring,
  team routing, on-call assignment.
- **Incident lifecycle** — create → acknowledge → resolve, with a complete timeline of every
  state change, escalation, and correlated alert.
- **Explainable severity scoring** — threshold ratio + alert frequency + team criticality,
  fully deterministic and inspectable (no black-box model).
- **Alert correlation** — related alerts on the same team within a configurable time window
  group into a single incident.
- **Rate-based escalation** — severity automatically climbs a tier after repeated
  alerts on the same incident.
- **Ack-timeout auto-escalation** — a background scheduler reassigns unacknowledged incidents
  to the backup on-call engineer once they've overrun their team's escalation window.
- **Linked runbooks** — team- and metric-pattern-matched runbooks (title, URL, ordered steps)
  surfaced on the incident detail view.
- **Slack notifications** — on incident creation, severity escalation, and resolution.
- **MTTR & metrics reporting** — `/metrics` reports totals, breakdowns by status/severity, and
  average resolution time.
- **React + TypeScript dashboard** — incident list/filters, incident detail with actions,
  escalation policy management, and a metrics overview.
- **Infrastructure as code** — Kubernetes manifests and Terraform targeting GKE + Cloud SQL for
  a production deployment on GCP.

## Architecture

```mermaid
flowchart LR
    subgraph Monitoring
        M[Prometheus / Datadog / PagerDuty]
    end

    subgraph Backend [FastAPI backend]
        ING["POST /alerts/ingest"]
        CORR[Dedup & correlate]
        SEV[Severity scoring]
        ROUTE[Team routing +\non-call lookup]
        DB[(PostgreSQL)]
        SCHED[APScheduler:\nack-timeout escalation]
        API[Incidents / Escalation /\nRunbooks API]
    end

    FE[React + Vite SPA]
    SLACK[Slack]

    M -->|structured alert| ING --> CORR --> SEV --> ROUTE --> DB
    ROUTE -->|notify| SLACK
    SCHED -->|poll overdue incidents| DB
    SCHED -->|notify| SLACK
    FE -->|REST| API --> DB
>>>>>>> Stashed changes
```

The frontend never talks to Postgres directly — everything goes through the FastAPI backend.
The escalation scheduler runs inside the API process and polls the same database on an
interval; it isn't a separate service.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2, APScheduler |
| Database | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, react-router-dom |
| Notifications | Slack incoming webhooks |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes (GKE) |
| Infrastructure as code | Terraform (`hashicorp/google`) |
| CI/CD | GitHub Actions |
| Testing | pytest (against real PostgreSQL, no mocks) |

## Project structure

```
backend/
  app/
    main.py               FastAPI app, health + metrics endpoints, escalation scheduler
    models.py              SQLAlchemy ORM models (Incident, Alert, EscalationPolicy,
                            IncidentTimeline, RunBook)
    database.py             Engine/session setup
    config.py                Environment-driven settings
    routers/                   incidents, alerts, escalation, runbooks endpoints
    services/                    business logic (incident, routing, runbook, Slack)
    schemas/                       Pydantic request/response models
  tests/                    pytest suite (real Postgres, no mocking)
  Dockerfile
  requirements.txt
database/
  schema.sql               Tables, indexes, triggers, stored procedure
  init.sql                  Seed data (escalation policies, runbooks)
frontend/
  src/
    api/                    Typed API client (client.ts, types.ts)
    components/              Nav, severity/status badges
    pages/                     Dashboard, IncidentDetail, EscalationPolicies, Metrics
  Dockerfile                nginx-served static build
kubernetes/                Deployment, Service, ConfigMap, Secret template for GKE
terraform/                 GCP infra: VPC, GKE cluster + node pool, Cloud SQL Postgres
.github/workflows/ci.yml   Backend tests + frontend build + Docker image builds
docker-compose.yml         Local dev: Postgres + API + frontend
```

## Getting started

### Prerequisites

- Docker + Docker Compose (this is the only hard requirement — Python and Node are not
  needed on the host, everything runs in containers)

### Quick start

```bash
cp .env.example .env          # optional: add a Slack webhook for real notifications
docker-compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000 (interactive docs at `/docs`, health check at `/health`)
- Postgres: `localhost:5432` (`incidents_user` / `incidents_password`)

Postgres is initialized automatically from `database/schema.sql` and `database/init.sql` via
`docker-entrypoint-initdb.d` **on first container start only**. If you change the schema, reset
the volume to pick it up: `docker-compose down -v && docker-compose up --build`.

Try it end to end:

```bash
curl -X POST http://localhost:8000/alerts/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "prometheus", "metric_name": "db_connections", "threshold": 100, "current_value": 450}'
```

Then refresh http://localhost:8080 to see the incident appear.

### Frontend, without Docker

For hot-reload iteration (requires Node 20+ installed locally):

```bash
cd frontend
cp .env.example .env      # VITE_API_BASE_URL, defaults to http://localhost:8000
npm install
npm run dev
```

## API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/alerts/ingest` | Ingest a monitoring alert; dedups/correlates, scores severity, routes, creates or updates an incident |
| `POST` | `/incidents` | Create an incident directly |
| `GET` | `/incidents` | List incidents (filter by `status`, `severity`, `team`) |
| `GET` | `/incidents/{id}` | Incident detail — full record, alerts, timeline |
| `PATCH` | `/incidents/{id}` | Update status, assigned engineer, or tags |
| `POST` | `/incidents/{id}/acknowledge` | Acknowledge an incident |
| `POST` | `/incidents/{id}/resolve` | Resolve an incident (with optional resolution summary) |
| `GET` | `/incidents/{id}/runbook` | Best-matching runbook for this incident (404 if none) |
| `GET` | `/escalation-policies` | List escalation policies |
| `POST` | `/escalation-policies` | Create a policy (409 on duplicate team+severity) |
| `PATCH` | `/escalation-policies/{id}` | Update a policy |
| `GET` | `/runbooks` | List runbooks (optionally filter by `team`) |
| `POST` | `/runbooks` | Create a runbook (409 on duplicate team+metric pattern) |
| `PATCH` | `/runbooks/{id}` | Update a runbook |
| `GET` | `/metrics` | Total/open incident counts, breakdowns by status/severity, average MTTR |
| `GET` | `/health` | Liveness/readiness check |

Full request/response examples:

```bash
# Create an incident directly
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"title": "Database down", "description": "RDS unreachable", "severity": "CRITICAL", "team": "data-platform"}'

# List incidents
curl http://localhost:8000/incidents

# Acknowledge
curl -X POST http://localhost:8000/incidents/{id}/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"engineer_name": "arjun"}'

# Resolve
curl -X POST http://localhost:8000/incidents/{id}/resolve \
  -H "Content-Type: application/json" \
  -d '{"resolution_summary": "Restarted RDS connection pool"}'

# Linked runbook
curl http://localhost:8000/incidents/{id}/runbook
```

Or just open http://localhost:8000/docs for the full interactive Swagger UI:

![Interactive API docs](docs/screenshots/api-docs.png)

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://incidents_user:incidents_password@localhost:5432/incidents` |
| `SLACK_WEBHOOK_URL` | Incoming webhook for Slack notifications | unset (notifications are skipped and logged) |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `PORT` | API port | `8000` |
| `ALERT_CORRELATION_WINDOW_MINUTES` | Time window for grouping related alerts on the same team into one incident | `15` |
| `ESCALATION_CHECK_INTERVAL_SECONDS` | How often the background job checks for overdue unacknowledged incidents | `60` |
| `VITE_API_BASE_URL` (frontend, build-time) | Base URL the SPA calls for the API | `http://localhost:8000` |

`SLACK_WEBHOOK_URL` should never be committed — set it locally in `.env` (gitignored) or as a
<<<<<<< Updated upstream
GitHub Actions secret in CI/CD.
=======
GitHub Actions secret in CI/CD. `VITE_API_BASE_URL` is inlined by Vite at build time, so for
Docker it's passed as a build arg (see `docker-compose.yml`), not a runtime env var.

## Design notes

**Why severity scoring is a heuristic, not a trained ML model.** A real classifier needs
labeled examples — (alert features → the severity that turned out to be correct) — to learn
from. This system has no historical incident data yet, and training on synthetic data would
just re-encode whatever assumption went into generating it, dressed up as a model. So
`determine_severity_from_threshold()` (in `backend/app/services/incident_service.py`) is a
deterministic, fully explainable scoring function: threshold-breach ratio sets a base score,
repeated-alert frequency and team business-criticality can each raise it a tier, clamped to
LOW–CRITICAL. Once the system has generated its own labeled incident history, a real model
becomes viable as a drop-in replacement behind the same function signature.

**Why alert correlation has two tiers.** Exact `metric_name` matching against an open incident
is cheap and precise, so it's tried first. The fallback — same team, within
`ALERT_CORRELATION_WINDOW_MINUTES` — catches the common case where a single underlying problem
trips multiple different metrics (e.g. `payment_latency` and `payment_errors` firing together)
without over-merging unrelated incidents from the same team hours apart.

**Why runbooks are links, not an execution engine.** `RunBook` stores a title, URL, and ordered
steps — a reference checklist a human follows. It deliberately does not execute commands or
scripts on an incident's behalf.

## Testing

Tests run against a real PostgreSQL instance — no mocking, matching what CI does:

```bash
# with docker-compose up already running:
docker-compose exec api pytest tests/ -v

# or standalone, against any Postgres reachable via DATABASE_URL:
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Formatting:

```bash
docker-compose exec api black --check app/
```

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`/`develop`:

- **test** — spins up Postgres, applies `schema.sql`/`init.sql`, runs the full pytest suite,
  checks `black` formatting.
- **frontend** — `npm install`, typecheck (`tsc -b --noEmit`), `npm run build`.
- **build** (main only, after test + frontend pass) — builds the API and frontend Docker
  images.

## Infrastructure & deployment (GCP)

`terraform/` provisions a VPC, a GKE cluster + node pool, and a Cloud SQL for PostgreSQL
instance on a private IP connected to that VPC. `kubernetes/` runs the API on that cluster
(Deployment, Service, ConfigMap, Secret template).

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in project_id, then set db_password separately
terraform init
terraform plan -var="db_password=<your-password>"
terraform apply -var="db_password=<your-password>"
```

`db_password` has no default and should never be committed — pass it via `-var`, an
environment variable (`TF_VAR_db_password`), or a CI secret.

After `apply`, get cluster credentials and deploy the API:

```bash
gcloud container clusters get-credentials $(terraform output -raw gke_cluster_name) --zone <zone>

kubectl apply -f kubernetes/configmap.yaml
kubectl create secret generic incident-api-secrets \
  --from-literal=DATABASE_URL="$(terraform output -raw database_url)" \
  --from-literal=SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

`kubernetes/secrets.yaml` is a template only (placeholder values) — real secrets are created
imperatively as shown above, or via a secret manager integration, never committed as YAML. The
frontend isn't part of the Kubernetes/Terraform setup yet (see [Roadmap](#roadmap)) — it can be
built with `VITE_API_BASE_URL` pointed at the GKE-hosted API's external address and served from
any static host or an additional Deployment.

## Roadmap

- Deploy the current stack to a real GCP project (Terraform apply + `kubectl apply`) — the
  infrastructure code exists and is validated, but hasn't been pointed at a live project yet.
- Add the frontend to the Kubernetes/Terraform setup for a full in-cluster deployment.
- Real ML-based severity classification, once the system has accumulated enough of its own
  labeled incident history to train on.
- Maintenance windows / alert silencing.
>>>>>>> Stashed changes
