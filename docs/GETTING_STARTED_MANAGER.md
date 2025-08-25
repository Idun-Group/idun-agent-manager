# Getting Started: Idun Agent Manager (Local MVP)

This guide shows how to run Traefik, Postgres, and the Idun Agent Manager locally with Docker Compose and deploy a simple agent.

## Prerequisites

- Docker Desktop (or Docker Engine) running
- Make sure ports 80, 8080, 5432 are free

## Start the stack

From the repo root:

```bash
docker compose up --build -d
```

Services:

- Traefik: `http://localhost:8080` (dashboard)
- Postgres: on `localhost:5432` (db `idun_manager`, user `postgres`, password `postgres`)
- Idun Agent Manager API: proxied via Traefik at `http://localhost/api/v1` (docs at `http://localhost/docs`)

## Verify the API

Open `http://localhost/docs` and confirm the OpenAPI UI loads.

## Create a Managed Agent

The manager expects three configs: engine, retrieval, deployment.

Example request (GitHub retrieval + local deployment):

```bash
curl -X POST http://localhost/api/v1/agents/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "hello-agent",
    "description": "Sample agent",
    "engine": {"config": {"agent": {"type": "langgraph", "config": {"name": "Hello"}}, "server": {"api": {"port": 8000}}}},
    "retrieval": {"type": "github", "repo": "geoffreyharrazi/idun-agent-manager", "ref": "main", "path": "libs/idun_agent_engine/examples/03_minimal_setup"},
    "deployment": {"type": "local"}
  }'
```

List agents:

```bash
curl http://localhost/api/v1/agents/
```

## Build and Deploy

```bash
curl -X POST http://localhost/api/v1/agents/<AGENT_ID>/deploy
```

Check versions and deployments:

```bash
curl http://localhost/api/v1/agents/<AGENT_ID>/versions
curl http://localhost/api/v1/agents/<AGENT_ID>/deployments
```

The deployed agent will be reachable under a path like:

```text
http://localhost/api/v1/agents/agent-<AGENT_ID>
```

## Rollback

```bash
curl -X POST http://localhost/api/v1/agents/<AGENT_ID>/rollback/<VERSION_NUMBER>
```

## Tear down

```bash
docker compose down -v
```
