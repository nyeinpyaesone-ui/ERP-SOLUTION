# DevContainer

This development environment uses Docker Compose to provide the Django workspace,
PostgreSQL 15, and Redis 7 on one private Compose network.

## Start

Open the repository in VS Code and run **Dev Containers: Rebuild and Reopen in
Container**. The app service waits for healthy database/cache services before
the post-create script installs development dependencies, applies migrations,
and runs Django's system check.

## Run the application

```bash
python src/manage.py runserver 0.0.0.0:8000
python -m pytest
```

## Local configuration

Compose uses local-only fallback credentials so a first-time checkout can start
without a secrets file. Override them with `DEV_DB_PASSWORD` and
`DEV_SECRET_KEY` in the shell environment or a local, untracked Compose
environment file. Never reuse these values outside local development.

PostgreSQL data is stored in the named `postgres-data` volume and survives
container rebuilds. To intentionally reset the local database, remove that
volume with `docker compose -f .devcontainer/compose.yaml down -v`; this
permanently deletes local development data.

The Docker-outside-of-Docker feature and host SSH-directory mount are omitted
by default: both grant the container access to sensitive host capabilities.
Add them only when a concrete development task requires them and the access
risk is understood.
