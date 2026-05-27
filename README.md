# Cairn

Reusable FastAPI template for agentic Python applications with LangGraph.

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
make lint            # ruff check
make check           # lint + test
```

## Structure

```
config/     YAML config, prompts, loader
db/         SQLAlchemy models, Alembic migrations
memory/     Vector store backends (FAISS, pgvector, Pinecone)
cache/      Key-value backends (in-memory, Redis)
assets/     File storage backends (local, S3)
lib/        Raw AWS clients
scripts/    CLI scripts and DB seeding
src/        Application code
  agents/   LLM agent builders
  evals/    LLM-as-judge framework
  graphs/   LangGraph workflow factories
  jobs/     Background job scheduler
  models/   Pydantic schemas and state
  policies/ RBAC authorization
  routers/  FastAPI endpoints
  security/ Auth and input validation
  services/ Service registry and protocol
  tools/    Tool registry and context
  utils/    Logging, datetime, pagination, serialization
  websockets/ Connection manager and WS endpoint
tests/      Mirrors src/ structure
```

## Configuration

Three-level hierarchy with deep merge:

```
.env.default → .env.{APP_ENV}          (environment variables)
config/default.yaml → config/graphs/X.yaml  (YAML config)
Runtime overrides                        (explicit params)
```

## Optional Dependencies

```bash
poetry install --with aws       # boto3 (S3 storage)
poetry install --with redis     # redis (cache backend)
poetry install --with pinecone  # pinecone-client (vector store)
poetry install --with pgvector  # pgvector (PostgreSQL vector store)
```

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
Create a tool in `src/tools/my_tool.py` and it's automatically registered - no manual imports needed.

### Singleton Backends
Memory, cache, and storage backends use singleton pattern - data persists across requests.

### Config-Driven Graphs
Define model, tools, and settings in YAML - swap configurations without code changes.

### Test Infrastructure
Comprehensive fixtures with FastAPI dependency overrides - tests run in parallel safely.

### Multi-Environment Support
`.env.{APP_ENV}` hierarchy with environment switching and settings caching.
