# Idun Agent Manager

A service that retrieves agent projects, builds container images using Idun Agent Engine, deploys them (local/GCP/K8s in future), manages routing via Traefik, and persists configurations and history in Postgres.

## Role in the Platform

- Orchestrates the lifecycle of agents: retrieve → build → push → deploy → route → persist
- Provides CRUD API for managed agents, tracks versions and deployments, and enables rollbacks.
- Declares Traefik routes (via labels when deploying) so that each agent is accessible through the gateway.

## Architecture (MVP)

- Web: FastAPI routers under `web/`
- Domain: Pydantic schemas in `domain/`
- Providers: pluggable retrievers (local zip, GitHub), deployers (local Docker), registries (local no-op)
- Storage: SQLAlchemy models for Postgres: `managed_agents`, `agent_versions`, `deployments`
- Services: `agent_service.py` for build/deploy/versioning orchestration

Flow:

1. Create Managed Agent with engine/retrieval/deployment configs
2. Deploy: retrieve source → write `config.yaml` → ensure Dockerfile → build image → push (local) → deploy (Docker) with Traefik labels → record version + deployment
3. Route: Traefik matches `/api/v1/agents/agent-<ID>` to the container
4. Persist: configurations, versions, deployments in Postgres

## Running Locally

Use the root `docker-compose.yml`:

```bash
docker compose up --build -d
```

- Manager API: `http://localhost/api/v1` (docs at `/docs`)
- Traefik dashboard: `http://localhost:8080`
- Postgres: `postgres://postgres:postgres@localhost:5432/idun_manager`

## API Overview

- POST `/api/v1/agents/` create
- GET `/api/v1/agents/` list
- GET `/api/v1/agents/{id}` get
- PATCH `/api/v1/agents/{id}` update
- DELETE `/api/v1/agents/{id}` delete
- POST `/api/v1/agents/{id}/deploy` build and deploy new version
- GET `/api/v1/agents/{id}/versions` version history
- POST `/api/v1/agents/{id}/rollback/{version}` redeploy previous version
- GET `/api/v1/agents/{id}/deployments` deployments

See `../../docs/GETTING_STARTED_MANAGER.md` for step-by-step usage.
