# Incident Response Automation

Automated incident ingestion and routing platform that reduces manual triage time by turning
raw monitoring alerts (Prometheus, Datadog, PagerDuty) into routed, tracked incidents with
Slack notifications and MTTR reporting.

## Phase 1: Foundation

- FastAPI backend backed by PostgreSQL
- Alert ingestion with automatic team routing and on-call assignment
- Incident lifecycle: create → acknowledge → resolve, with a full timeline
- Slack notifications on incident creation and resolution
- Docker Compose for local development, GitHub Actions for CI

## Phase 2 (current): Infrastructure

- Kubernetes manifests to run the API on GKE (Deployment, Service, ConfigMap, Secret template)
- Terraform IaC targeting GCP: GKE cluster + node pool, Cloud SQL for PostgreSQL on a private VPC connection

A frontend UI and advanced alerting are planned for later phases.

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
kubernetes/             Deployment, Service, ConfigMap, Secret template for GKE
terraform/              GCP infra: VPC, GKE cluster, Cloud SQL Postgres
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

## Infrastructure (GCP)

`terraform/` provisions a VPC, a GKE cluster, and a Cloud SQL for PostgreSQL instance on a
private IP connected to that VPC.

```
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in project_id, then set db_password separately
terraform init
terraform plan -var="db_password=<your-password>"
terraform apply -var="db_password=<your-password>"
```

`db_password` has no default and should never be committed — pass it via `-var`, an
environment variable (`TF_VAR_db_password`), or a CI secret.

After `apply`, get cluster credentials and deploy the API:

```
gcloud container clusters get-credentials $(terraform output -raw gke_cluster_name) --zone <zone>

kubectl apply -f kubernetes/configmap.yaml
kubectl create secret generic incident-api-secrets \
  --from-literal=DATABASE_URL="$(terraform output -raw database_url)" \
  --from-literal=SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

`kubernetes/secrets.yaml` is a template only (placeholder values) — real secrets are created
imperatively as shown above, or via a secret manager integration, never committed as YAML.
