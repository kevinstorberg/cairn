# Multi-Environment Deployment Guide

Cairn supports multiple environments (development, test, production) with a hierarchical configuration system. This guide covers setup, secrets management, and deployment patterns.

## Table of Contents

- [Environment Configuration](#environment-configuration)
- [Setting Up Environments](#setting-up-environments)
- [Secrets Management](#secrets-management)
- [Docker Deployment](#docker-deployment)
- [Database Migrations](#database-migrations)
- [Backend Configuration](#backend-configuration)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Environment Configuration

### Configuration Hierarchy

Cairn loads configuration in this order (later overrides earlier):

1. `.env.default` - Committed defaults for all environments
2. `.env.{APP_ENV}` - Environment-specific overrides (e.g., `.env.production`)
3. Environment variables - Runtime overrides (highest priority)

**Example**:
```bash
# .env.default (committed to git)
APP_ENV=development
DATABASE_URL_DEVELOPMENT=postgresql+asyncpg://localhost:5432/cairn_dev
MEMORY_BACKEND=faiss
CACHE_BACKEND=memory
STORAGE_BACKEND=local
LOG_LEVEL=INFO

# .env.production (NOT committed - see .gitignore)
DATABASE_URL_PRODUCTION=postgresql+asyncpg://prod-db:5432/cairn_prod
MEMORY_BACKEND=pgvector
CACHE_BACKEND=redis
REDIS_URL=redis://prod-redis:6379/0
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
LOG_LEVEL=WARNING

# Environment variable (runtime override)
export DATABASE_URL_PRODUCTION="postgresql+asyncpg://new-host:5432/cairn_prod"
```

### APP_ENV Variable

The `APP_ENV` variable determines which environment-specific file is loaded:

```bash
# Development (default)
APP_ENV=development  # Loads .env.development

# Testing
APP_ENV=test  # Loads .env.test

# Production
APP_ENV=production  # Loads .env.production
```

---

## Setting Up Environments

### Development Environment

**Goal**: Fast iteration, local services, verbose logging

**Setup**:
```bash
# 1. Copy default environment file
cp .env.default .env.development

# 2. Start local services
docker-compose up -d postgres

# 3. Run migrations
poetry run alembic upgrade head

# 4. Start development server
poetry run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

**Configuration** (`.env.development`):
```bash
APP_ENV=development
DATABASE_URL_DEVELOPMENT=postgresql+asyncpg://localhost:5432/cairn_dev

# Local backends
MEMORY_BACKEND=faiss
MEMORY_STORE_PATH=./memory_store
CACHE_BACKEND=memory
STORAGE_BACKEND=local
STORAGE_PATH=./storage

# Verbose logging
LOG_LEVEL=DEBUG
```

---

### Test Environment

**Goal**: Isolated database, fast tests, no external dependencies

**Setup**:
```bash
# 1. Create test environment file
cat > .env.test << EOF
APP_ENV=test
DATABASE_URL_TEST=postgresql+asyncpg://localhost:5432/cairn_test
MEMORY_BACKEND=faiss
CACHE_BACKEND=memory
STORAGE_BACKEND=local
LOG_LEVEL=WARNING
EOF

# 2. Create test database
createdb cairn_test

# 3. Run migrations
APP_ENV=test poetry run alembic upgrade head

# 4. Run tests
poetry run pytest
```

**Configuration** (`.env.test`):
```bash
APP_ENV=test
DATABASE_URL_TEST=postgresql+asyncpg://localhost:5432/cairn_test

# Fast local backends
MEMORY_BACKEND=faiss
CACHE_BACKEND=memory
STORAGE_BACKEND=local

# Minimal logging in tests
LOG_LEVEL=WARNING
```

---

### Production Environment

**Goal**: Scalable, persistent, secure, monitored

**Setup**:
```bash
# 1. Create production environment file (DO NOT COMMIT)
cat > .env.production << EOF
APP_ENV=production
DATABASE_URL_PRODUCTION=postgresql+asyncpg://prod-db.internal:5432/cairn_prod

# Production backends
MEMORY_BACKEND=pgvector
CACHE_BACKEND=redis
REDIS_URL=redis://prod-redis.internal:6379/0
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
S3_BUCKET=cairn-prod-storage

# API keys (use secrets manager in real deployment)
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Production logging
LOG_LEVEL=WARNING
EOF

# 2. Run migrations
APP_ENV=production poetry run alembic upgrade head

# 3. Start with gunicorn (production WSGI server)
poetry run gunicorn src.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**Configuration** (`.env.production`):
```bash
APP_ENV=production
DATABASE_URL_PRODUCTION=postgresql+asyncpg://prod-db.internal:5432/cairn_prod

# Production backends
MEMORY_BACKEND=pgvector
CACHE_BACKEND=redis
REDIS_URL=redis://prod-redis.internal:6379/0
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
S3_BUCKET=cairn-prod-storage

# Secrets (use secrets manager)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

# Production settings
LOG_LEVEL=WARNING
WORKERS=4
```

---

## Secrets Management

### DO NOT Commit Secrets

**Always in `.gitignore`**:
```gitignore
.env.production
.env.*.local
*.key
*.pem
secrets/
```

### Option 1: Environment Variables (Simple)

**Good for**: Small deployments, simple setups

```bash
# Set in shell
export ANTHROPIC_API_KEY="sk-ant-..."
export AWS_SECRET_ACCESS_KEY="..."

# Start app (reads from environment)
poetry run uvicorn src.app:app
```

### Option 2: Docker Secrets (Docker Swarm)

**Good for**: Docker deployments, multi-service apps

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: cairn:latest
    secrets:
      - anthropic_api_key
      - aws_secret_key
    environment:
      ANTHROPIC_API_KEY_FILE: /run/secrets/anthropic_api_key
      AWS_SECRET_ACCESS_KEY_FILE: /run/secrets/aws_secret_key

secrets:
  anthropic_api_key:
    external: true
  aws_secret_key:
    external: true
```

**Modified `src/settings.py`**:
```python
class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = Field(default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from file if path provided
        if key_file := os.getenv("ANTHROPIC_API_KEY_FILE"):
            self.ANTHROPIC_API_KEY = Path(key_file).read_text().strip()
```

### Option 3: AWS Secrets Manager (Production)

**Good for**: AWS deployments, team environments, key rotation

```python
# src/secrets.py
import boto3
import json

def load_secrets():
    """Load secrets from AWS Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='cairn/production')
    secrets = json.loads(response['SecretString'])

    for key, value in secrets.items():
        os.environ[key] = value
```

**Usage**:
```python
# src/app.py
from src.secrets import load_secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load secrets before anything else
    if get_settings().APP_ENV == "production":
        load_secrets()

    # ... rest of startup
    yield
```

---

## Docker Deployment

### Development Docker Compose

**File**: `docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cairn_dev
      POSTGRES_USER: cairn
      POSTGRES_PASSWORD: cairn_dev_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    command: poetry run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
    environment:
      APP_ENV: development
      DATABASE_URL_DEVELOPMENT: postgresql+asyncpg://cairn:cairn_dev_pass@postgres:5432/cairn_dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - postgres

volumes:
  postgres_data:
```

**Usage**:
```bash
docker-compose -f docker-compose.dev.yml up
```

---

### Production Docker Compose

**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  app:
    image: cairn:${VERSION:-latest}
    command: gunicorn src.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      APP_ENV: production
      DATABASE_URL_PRODUCTION: postgresql+asyncpg://cairn:${DB_PASSWORD}@postgres:5432/cairn_prod
      REDIS_URL: redis://redis:6379/0
      MEMORY_BACKEND: pgvector
      CACHE_BACKEND: redis
      STORAGE_BACKEND: s3
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cairn_prod
      POSTGRES_USER: cairn
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "cairn"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**Usage**:
```bash
# Build image
docker build -t cairn:v1.0.0 .

# Deploy
VERSION=v1.0.0 DB_PASSWORD=secure_password docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec app poetry run alembic upgrade head

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

---

### Dockerfile

**File**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.0

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev dependencies in production)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 cairn && chown -R cairn:cairn /app
USER cairn

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["gunicorn", "src.app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## Database Migrations

### Development Workflow

```bash
# 1. Make model changes
# Edit db/models/*.py

# 2. Generate migration
poetry run alembic revision --autogenerate -m "Add user table"

# 3. Review generated migration
cat alembic/versions/xxxx_add_user_table.py

# 4. Apply migration
poetry run alembic upgrade head

# 5. Rollback if needed
poetry run alembic downgrade -1
```

### Production Migration Strategy

**Option 1: Blue-Green Deployment (Zero Downtime)**

```bash
# 1. Deploy new version (blue) alongside old (green)
docker-compose -f docker-compose.prod.yml up -d --scale app=2

# 2. Run migrations (compatible with both versions)
docker-compose -f docker-compose.prod.yml exec app poetry run alembic upgrade head

# 3. Switch traffic to new version
# (Update load balancer, nginx, etc.)

# 4. Stop old version
docker-compose -f docker-compose.prod.yml scale app=1
```

**Option 2: Maintenance Window**

```bash
# 1. Put app in maintenance mode
# (Update nginx to serve maintenance page)

# 2. Stop app
docker-compose -f docker-compose.prod.yml stop app

# 3. Backup database
pg_dump cairn_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 4. Run migrations
docker-compose -f docker-compose.prod.yml run --rm app poetry run alembic upgrade head

# 5. Start app
docker-compose -f docker-compose.prod.yml up -d app

# 6. Remove maintenance mode
```

### Migration Safety Checklist

Before running migrations in production:

- [ ] Backward compatible? (New version works with old schema)
- [ ] Forward compatible? (Old version works with new schema)
- [ ] Database backup exists?
- [ ] Rollback plan tested?
- [ ] Migration tested in staging environment?
- [ ] No data loss? (Check DROP statements)
- [ ] Indexes added concurrently? (PostgreSQL `CREATE INDEX CONCURRENTLY`)
- [ ] Large table migrations tested for duration? (ALTER TABLE locks table)

---

## Backend Configuration

### Development → Production Checklist

#### Memory Backend

**Development** (`.env.development`):
```bash
MEMORY_BACKEND=faiss
MEMORY_STORE_PATH=./memory_store
```

**Production** (`.env.production`):
```bash
MEMORY_BACKEND=pgvector
DATABASE_URL_PRODUCTION=postgresql+asyncpg://prod-db:5432/cairn_prod
```

**Migration steps**:
1. Install pgvector extension: `CREATE EXTENSION vector;`
2. Export FAISS data (if any) before switching
3. Change environment variable
4. Test semantic search functionality

---

#### Cache Backend

**Development** (`.env.development`):
```bash
CACHE_BACKEND=memory
```

**Production** (`.env.production`):
```bash
CACHE_BACKEND=redis
REDIS_URL=redis://prod-redis:6379/0
```

**Migration steps**:
1. Deploy Redis instance
2. Change environment variable
3. No data migration needed (cache is ephemeral)
4. Test cache operations

---

#### Storage Backend

**Development** (`.env.development`):
```bash
STORAGE_BACKEND=local
STORAGE_PATH=./storage
```

**Production** (`.env.production`):
```bash
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=cairn-prod-storage
```

**Migration steps**:
1. Create S3 bucket
2. Set up IAM credentials
3. Run migration script to copy existing files:
```python
import asyncio
from pathlib import Path
from assets.backends import get_storage_backend

async def migrate_to_s3():
    local_path = Path("./storage")

    # Switch to S3
    os.environ["STORAGE_BACKEND"] = "s3"
    s3_storage = get_storage_backend()

    # Upload all local files
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            relative_key = str(file_path.relative_to(local_path))
            content = file_path.read_bytes()
            await s3_storage.upload(relative_key, content, "application/octet-stream")
            print(f"Migrated: {relative_key}")

asyncio.run(migrate_to_s3())
```
4. Test file upload/download

---

## Health Checks

### Basic Health Endpoint

**Already implemented** in `src/routes/health.py`:

```python
@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
```

### Advanced Health Check

**Add to `src/routes/health.py`**:

```python
from db.connection import get_session_factory
from cache.backends import get_cache_backend
from memory.backends import get_backend

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with backend status."""
    status = {
        "status": "ok",
        "database": "unknown",
        "cache": "unknown",
        "memory": "unknown"
    }

    # Check database
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute("SELECT 1")
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check cache
    try:
        cache = get_cache_backend()
        await cache.set("health_check", "ok", ttl=10)
        value = await cache.get("health_check")
        if value == "ok":
            status["cache"] = "ok"
        else:
            status["cache"] = "error: value mismatch"
    except Exception as e:
        status["cache"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check memory backend
    try:
        backend = get_backend()
        # Just check if backend is initialized
        status["memory"] = "ok"
    except Exception as e:
        status["memory"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return status
```

**Usage**:
```bash
# Basic check
curl http://localhost:8000/health

# Detailed check
curl http://localhost:8000/health/detailed
```

---

## Troubleshooting

### "Cannot connect to database"

**Problem**: App can't reach PostgreSQL.

**Solutions**:
```bash
# Check database is running
docker-compose ps postgres

# Check connection string
echo $DATABASE_URL_PRODUCTION

# Test connection manually
psql $DATABASE_URL_PRODUCTION

# Check firewall/security groups (cloud deployments)
```

---

### "Redis connection refused"

**Problem**: Cache backend can't reach Redis.

**Solutions**:
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u $REDIS_URL ping

# Check Redis URL format
# Correct: redis://hostname:6379/0
# Wrong: redis://hostname:6379 (missing db number)
```

---

### "S3 access denied"

**Problem**: Storage backend lacks S3 permissions.

**Solutions**:
```bash
# Check IAM credentials
aws sts get-caller-identity

# Test bucket access
aws s3 ls s3://$S3_BUCKET

# Verify IAM policy includes:
# - s3:PutObject
# - s3:GetObject
# - s3:DeleteObject
# - s3:ListBucket
```

---

### "Migration failed: relation already exists"

**Problem**: Running migrations on non-empty database.

**Solutions**:
```bash
# Option 1: Mark current schema as baseline
poetry run alembic stamp head

# Option 2: Drop all tables and start fresh (DEV ONLY!)
poetry run alembic downgrade base
poetry run alembic upgrade head

# Option 3: Manually fix schema mismatch
# Compare alembic versions table with actual migrations
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

---

### "Environment variables not loading"

**Problem**: Settings don't reflect environment changes.

**Solutions**:
```python
# In tests: Clear settings cache
from src.settings import reset_settings
reset_settings()

# Verify environment
import os
print(os.environ.get("APP_ENV"))

# Check .env file is being loaded
from src.settings import get_settings
settings = get_settings()
print(f"Loaded APP_ENV: {settings.APP_ENV}")
```

---

## Further Reading

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Docker Compose Production](https://docs.docker.com/compose/production/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
