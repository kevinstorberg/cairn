<img src="assets/static/logo.svg" alt="Cairn" width="120" align="left" style="margin-right: 20px; margin-bottom: 10px;"/>

# Cairn

FastAPI template for agentic Python applications with LangGraph, async SQLAlchemy,
vector memory, caching, tools, jobs, WebSockets, eval helpers, and local Docker
development.

This repository is a starting point. Clone it, keep the conventions that help,
and replace the application-specific parts with your own domain.

<br clear="left"/>

## Quick Start

```bash
poetry install
cp .env.default .env.development
docker compose up -d db
poetry run alembic upgrade head
poetry run uvicorn src.app:app --reload
```

If local port `5432` is busy:

```bash
POSTGRES_PORT=55432 docker compose up -d db
```

## Source Of Truth

Avoid duplicating these values in docs or app code:

| Concern | Authoritative location |
| --- | --- |
| Runtime environment and secrets | [.env.default](.env.default), [src/settings.py](src/settings.py) |
| Structural YAML config | [config/default.yaml](config/default.yaml), [config/models.py](config/models.py) |
| Graph-specific config | `config/graphs/*.yaml`, [config/loader.py](config/loader.py) |
| Database sessions and engines | [db/connection.py](db/connection.py) |
| Database model base classes | [db/base.py](db/base.py) |
| Backend protocols and factories | `memory/`, `cache/`, `assets/` |
| HTTP routes | [src/routers/](src/routers) |
| JWT auth | [src/security/auth.py](src/security/auth.py) |
| RBAC policy rules | [src/policies/base.py](src/policies/base.py), [src/policies/roles.py](src/policies/roles.py) |
| FastAPI policy dependencies | [src/policies/dependencies.py](src/policies/dependencies.py) |
| Test commands and markers | [Makefile](Makefile), [pyproject.toml](pyproject.toml) |
| Bootstrap checks | [scripts/doctor.py](scripts/doctor.py), [Makefile](Makefile) |
| Security automation | [.github/dependabot.yml](.github/dependabot.yml), [.github/workflows/security.yml](.github/workflows/security.yml) |

## Commands

```bash
make test
make test-unit
make test-e2e
make test-cov
make lint
make format
make format-check
make lock-check
make doctor
make check
```

The Makefile is the command reference. Keep new quality gates there instead of
adding parallel command lists elsewhere.

## Conventions

- Put application models under `db/models/`, schemas under `src/models/`, and
  route handlers under `src/routers/`.
- Keep routers thin. Route handlers should validate transport concerns and call
  services, repositories, tools, or graph builders for real work.
- Use `get_session()` for request-scoped database access.
- Use backend protocols plus factories instead of importing concrete backends
  throughout application code.
- Put public tools in `src/tools/`. Every public module in that package is
  production auto-discovered, so keep examples in docs or tests.
- Use `require_permission()` from `src.policies.dependencies` for FastAPI routes.
  Keep pure authorization rules in `src.policies`.
- Keep graph behavior in app-specific graph builder modules. The built-in
  `build_graph_from_config()` is a deterministic config smoke graph.

## Configuration

Runtime and secret values come from `.env.default`, `.env.{APP_ENV}`, and real
environment variables. Structural settings such as backend selection and model
defaults come from YAML.

Use explicit `DATABASE_URL_DEVELOPMENT`, `DATABASE_URL_TEST`, or
`DATABASE_URL_PRODUCTION` only when the component `POSTGRES_*` fields are not
enough. Otherwise, `Settings.database_url_for(env)` assembles the URL.

## Documentation

- [Testing](docs/TESTING.md): fixture usage, test boundaries, and state cleanup.
- [Tools](docs/TOOLS.md): LangChain tool registration and async tool patterns.
- [Backends](docs/BACKENDS.md): memory, cache, and storage backend switching.
- [Graphs](docs/GRAPHS.md): graph builder conventions and config flow.
- [Deployment](docs/DEPLOYMENT.md): environment, migration, and runtime checklist.
- [Doctor Command](docs/DOCTOR.md): bootstrap checks for local and provider setup.
- [Security Automation](docs/SECURITY_AUTOMATION.md): dependency updates, audit scans, and secret scanning.
- [Database Patterns](db/PATTERNS.md): SQLAlchemy pitfalls worth keeping explicit.

Prefer updating the source-of-truth file over repeating details in documentation.
Add docs only when they explain a convention, tradeoff, or workflow that the code
does not make obvious.
