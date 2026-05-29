<img src="assets/static/logo.svg" alt="Cairn" width="120" align="left" style="margin-right: 20px; margin-bottom: 10px;"/>

# Cairn

Production-ready FastAPI template for building agentic Python applications with LangGraph.

**This is a template repository.** Clone it to start your own project with batteries-included infrastructure for agents, tools, vector memory, caching, and background jobs.

<br clear="left"/>

## Quick Start

```bash
poetry install
cp .env.default .env.development
docker compose up -d db
poetry run alembic upgrade head
poetry run uvicorn src.app:app --reload
```

## Commands

```bash
make test            # all tests
make test-unit       # fast, no external deps
make test-e2e        # full integration
make test-cov        # tests with coverage report
make lint            # ruff check
make format          # ruff format (apply)
make format-check    # ruff format (check only)
make check           # lint + format-check + test
```

## Structure

```
config/          YAML config, prompts, loader
  prompts/       Prompt template directory (load with config/prompts/loader.py)
db/              SQLAlchemy models, Alembic migrations
memory/          Vector store backends (FAISS, pgvector, Pinecone)
cache/           Key-value backends (in-memory, Redis)
assets/          File storage backends (local, S3) - template infrastructure
lib/             Shared utilities (paths, singleton pattern)
  cairn/         Cairn-specific utilities (singleton, stubs, paths)
scripts/         CLI scripts and database seeding
src/             Your application code
  agents/        LLM agent builders
  evals/         LLM-as-judge evaluation framework
  graphs/        LangGraph workflow definitions
  jobs/          Background job scheduler
  models/        Pydantic schemas and state definitions
  policies/      RBAC role-based authorization
  routers/       FastAPI HTTP endpoints
  security/      Authentication and request validation
  services/      Service registry and lifecycle management
  tools/         LangChain tool registry (auto-discovered)
  utils/         Logging, datetime, pagination, serialization
  websockets/    WebSocket connection manager
tests/           Test suite mirroring src/ structure
  conftest.py    Shared test fixtures (use these in your tests)
```

## Configuration

Three-level hierarchy with deep merge (later layers override earlier):

```
1. .env.default → .env.{APP_ENV}              Environment variables
2. config/default.yaml → config/graphs/*.yaml  YAML configuration
3. Runtime overrides                           Explicit parameters
```

**Environment Variables:** Set `APP_ENV=development` (default), `production`, or `test`. Loads corresponding `.env.{APP_ENV}` file.

**YAML Config:** Base settings in `config/default.yaml`, graph-specific overrides in `config/graphs/`. All config imported via `load_default_config()` or `load_graph_config(name)`.

## Optional Dependencies

```bash
poetry install --with aws       # boto3 (S3 storage)
poetry install --with redis     # redis (cache backend)
poetry install --with pinecone  # pinecone-client (vector store)
poetry install --with pgvector  # pgvector (PostgreSQL vector store)
```

## CI/CD Pipeline

GitHub Actions workflows run automatically on push and pull requests:

- **Test Workflow** (`.github/workflows/test.yml`) - Linting, formatting, tests with coverage
- **Pre-commit Workflow** (`.github/workflows/pre-commit.yml`) - Enforces code quality hooks

### Pre-commit Hooks (Optional Local Setup)

Install pre-commit hooks to run checks before each commit:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

**Note:** Pre-commit checks are enforced in CI/CD even if you don't install them locally.

## Documentation

Comprehensive guides for building applications with Cairn:

- **[Testing Guide](docs/TESTING.md)** - Test patterns, fixtures, mocking, parallel execution
- **[Tool Development](docs/TOOLS.md)** - Creating tools, registration, database access, best practices
- **[Backend Switching](docs/BACKENDS.md)** - Memory/cache/storage backends, migration guides
- **[Graph Development](docs/GRAPHS.md)** - Building LangGraph workflows, state management, node patterns
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Multi-environment setup, Docker, migrations, secrets management
- **[Database Patterns](db/PATTERNS.md)** - Common pitfalls, SQLAlchemy patterns, PostgreSQL specifics

## Key Features

### Auto-Discovery Tools
Create a tool in `src/tools/my_tool.py` with `@register_tool` and it's automatically available - no manual imports. See `src/tools/test_auto_import.py` for a complete example.

### Singleton Backends
Memory, cache, and storage backends use singleton pattern - instances persist across requests for performance.

### Config-Driven Graphs
Define LLM model, tools, and settings in YAML - swap entire configurations without code changes.

### Test Infrastructure
Production-quality test fixtures in `tests/conftest.py`: database setup, FastAPI client, session management. Ready for your integration tests.

### Template Utilities (Unused by Default)
- **`tests/conftest.py`** - Pytest fixtures for database and API testing
- **`config/prompts/loader.py`** - Load LLM prompts from .txt files
- **`src/routers/base.py`** - Router factory for consistent configuration
- **`assets/`** - File storage abstraction (local/S3)

These are intentionally unused by the template's example code but documented and ready for your application to activate.

### Multi-Environment Support
`.env.{APP_ENV}` hierarchy with automatic environment detection and config merging.
