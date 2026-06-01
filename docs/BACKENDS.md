# Backend Switching Guide

Cairn supports multiple backends for memory, cache, and storage. Switch between them
by changing `config/default.yaml`—no code changes required.

```yaml
# config/default.yaml
memory:
  backend: in_memory  # Options: in_memory, pgvector, pinecone

cache:
  backend: memory     # Options: memory, redis

storage:
  backend: local      # Options: local, s3
```

## Table of Contents

- [Memory Backends](#memory-backends)
- [Cache Backends](#cache-backends)
- [Storage Backends](#storage-backends)
- [Backend Comparison](#backend-comparison)
- [Migration Guide](#migration-guide)

---

## Memory Backends

Memory backends store vector embeddings for semantic search.

### In-Memory (Default - Local)

**Use when**: Development, single-server deployments, prototyping

**Setup** (`config/default.yaml`):
```yaml
memory:
  backend: in_memory
```

**Pros**:
- No external dependencies
- Fast queries
- Simple setup
- Free

**Cons**:
- In-memory only (lost on restart)
- Single-server only
- No persistence to disk

**Code example**:
```python
from memory.backends import get_backend

backend = get_backend()  # Returns InMemoryVectorBackend
await backend.store("id1", "text", {"key": "value"}, embedding)
results = await backend.search(query_embedding, limit=5)
```

---

### PGVector (PostgreSQL Extension)

**Use when**: Production, need persistence, already using PostgreSQL

**Setup** (`config/default.yaml`):
```yaml
memory:
  backend: pgvector
```

Also ensure the pgvector extension exists in your PostgreSQL:
```sql
CREATE EXTENSION vector;
```

**Install dependency**:
```bash
poetry install --with pgvector
```

**Pros**:
- Persistent storage
- Integrates with existing PostgreSQL
- ACID guarantees
- No additional infrastructure

**Cons**:
- Slower than in-memory for large datasets
- Requires PostgreSQL 11+
- Needs pgvector extension

**Migration from in-memory**:
```python
# 1. Export from in-memory backend
old_backend = get_backend()  # backend: in_memory
# Manually export vectors before switching

# 2. Update config/default.yaml to backend: pgvector
# 3. Restart app — get_backend() now returns PGVectorBackend
```

---

### Pinecone (Cloud Vector Database)

**Use when**: Large scale, multi-region, managed service

**Setup** (`config/default.yaml`):
```yaml
memory:
  backend: pinecone
```

Also set Pinecone credentials in your environment:
```bash
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=cairn-vectors
```

**Install dependency**:
```bash
poetry install --with pinecone
```

**Pros**:
- Fully managed
- Scales automatically
- Multi-region
- Real-time updates

**Cons**:
- Costs money
- External dependency
- Network latency

---

## Cache Backends

Cache backends store temporary key-value data for performance.

### Memory Cache (Default - Local)

**Use when**: Development, testing, single-server

**Setup** (`config/default.yaml`):
```yaml
cache:
  backend: memory
```

**Pros**:
- No dependencies
- Very fast
- Simple

**Cons**:
- Lost on restart
- Single-server only
- Limited capacity

**Code example**:
```python
from cache.backends import get_cache_backend

cache = get_cache_backend()  # Returns MemoryCacheBackend
await cache.set("key", "value", ttl=60)
value = await cache.get("key")
await cache.delete("key")
```

---

### Redis (Production)

**Use when**: Production, multiple servers, need persistence

**Setup** (`config/default.yaml`):
```yaml
cache:
  backend: redis
```

Also set Redis URL in your environment:
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# .env
REDIS_URL=redis://localhost:6379/0
```

**Install dependency**:
```bash
poetry install --with redis
```

**Pros**:
- Persistent (optional)
- Multi-server support
- Pub/sub capabilities
- Battle-tested

**Cons**:
- Requires Redis server
- Network overhead
- Operational complexity

**Migration from Memory**:
```yaml
# Just change config/default.yaml - no data migration needed
# Cache is ephemeral by nature
cache:
  backend: redis
```

---

## Storage Backends

Storage backends handle file uploads (attachments, images, etc.).

### Local Storage (Default)

**Use when**: Development, single-server, small files

**Setup** (`config/default.yaml`):
```yaml
storage:
  backend: local
  local_path: ./storage
```

**Pros**:
- No dependencies
- Simple
- Free
- Fast access

**Cons**:
- Single-server only
- No redundancy
- Limited scaling

**Code example**:
```python
from assets.backends import get_storage_backend

storage = get_storage_backend()  # Returns LocalStorageBackend
await storage.upload("todos/123/file.pdf", file_bytes, "application/pdf")
content = await storage.download("todos/123/file.pdf")
await storage.delete("todos/123/file.pdf")
```

---

### S3 (Production)

**Use when**: Production, multiple servers, need durability

**Setup** (`config/default.yaml`):
```yaml
storage:
  backend: s3
```

Also set AWS credentials in your environment:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=your-bucket-name
```

**Install dependency**:
```bash
poetry install --with aws
```

**Pros**:
- Highly durable (99.999999999%)
- Scales infinitely
- CDN integration
- Versioning support

**Cons**:
- Costs money
- Network latency
- External dependency

**Migration from Local**:
```python
import asyncio
from pathlib import Path
from assets.backends.s3 import S3Storage

async def migrate_to_s3():
    local_path = Path("./storage")
    s3_storage = S3Storage()

    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            relative_key = str(file_path.relative_to(local_path))
            content = file_path.read_bytes()
            await s3_storage.upload(relative_key, content, "application/octet-stream")
            print(f"Migrated: {relative_key}")

asyncio.run(migrate_to_s3())
# Then update config/default.yaml: storage.backend: s3
```

---

## Backend Comparison

### Memory Backends

| Feature | In-Memory | PGVector | Pinecone |
|---------|-----------|----------|----------|
| **Setup** | Easy | Medium | Easy |
| **Cost** | Free | Free | $$ |
| **Persistence** | No | Yes | Yes |
| **Scale** | Single server | DB limits | Unlimited |
| **Speed** | Fastest | Fast | Good |
| **Best for** | Dev, small | Production | Enterprise |

### Cache Backends

| Feature | Memory | Redis |
|---------|--------|-------|
| **Setup** | Easy | Medium |
| **Cost** | Free | Free/$ |
| **Persistence** | No | Optional |
| **Multi-server** | No | Yes |
| **Speed** | Fastest | Fast |
| **Best for** | Dev, test | Production |

### Storage Backends

| Feature | Local | S3 |
|---------|-------|-----|
| **Setup** | Easy | Medium |
| **Cost** | Free | $$ |
| **Durability** | Low | Very High |
| **Scale** | Limited | Unlimited |
| **Speed** | Fastest | Good |
| **Best for** | Dev | Production |

---

## Migration Guide

### Development → Production Checklist

#### Memory
- [ ] Choose backend: PGVector (if using PostgreSQL) or Pinecone (if scaling)
- [ ] Export existing in-memory vectors (if any)
- [ ] Update `config/default.yaml`: `memory.backend: pgvector` or `pinecone`
- [ ] Set credentials in environment (Pinecone API key, or ensure pgvector extension)
- [ ] Install dependencies (`--with pgvector` or `--with pinecone`)
- [ ] Import vectors to new backend
- [ ] Test semantic search

#### Cache
- [ ] Set up Redis server
- [ ] Update `config/default.yaml`: `cache.backend: redis`
- [ ] Set `REDIS_URL` in environment
- [ ] Install dependency (`--with redis`)
- [ ] No data migration needed (cache is ephemeral)
- [ ] Test cache operations

#### Storage
- [ ] Create S3 bucket
- [ ] Set up IAM credentials in environment
- [ ] Update `config/default.yaml`: `storage.backend: s3`
- [ ] Install dependency (`--with aws`)
- [ ] Run migration script to copy files
- [ ] Test file upload/download

### Configuration Reference

**Development** (`config/default.yaml`):
```yaml
memory:
  backend: in_memory
cache:
  backend: memory
storage:
  backend: local
  local_path: ./storage
```

**Production** (`config/default.yaml` or environment-specific override):
```yaml
memory:
  backend: pgvector    # or pinecone
cache:
  backend: redis
storage:
  backend: s3
```

**Secrets** (`.env.production` — not committed):
```bash
DATABASE_URL_PRODUCTION=postgresql+asyncpg://...
REDIS_URL=redis://your-redis:6379/0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=your-bucket
PINECONE_API_KEY=...          # if using Pinecone
PINECONE_ENVIRONMENT=...      # if using Pinecone
```

---

## Testing with Different Backends

Backend selection is driven by `config/default.yaml`. To test with different backends,
temporarily change the YAML config or use environment-specific config overrides:

### Test with defaults (in-memory + memory cache + local storage)
```bash
poetry run pytest
```

### Test with Redis (Integration)
```bash
docker run -d -p 6379:6379 redis:7-alpine
# Update config/default.yaml: cache.backend: redis
# Ensure REDIS_URL is set in .env.test
poetry run pytest
```

### Test with PGVector (Integration)
```bash
# Ensure pgvector extension is installed in test database
# Update config/default.yaml: memory.backend: pgvector
poetry run pytest
```

---

## Troubleshooting

### "Unknown backend" error

**Problem**: Backend name misspelled in `config/default.yaml` or dependency not installed.

**Solution**:
```bash
# Check config/default.yaml for valid values:
#   memory.backend: in_memory, pgvector, or pinecone
#   cache.backend: memory or redis
#   storage.backend: local or s3

# Install dependencies for non-default backends
poetry install --with pgvector  # or --with pinecone, --with redis, --with aws
```

### Memory backend not persisting data

**Problem**: Using in-memory backend (data lost on restart).

**Solution**: Switch to PGVector or Pinecone for persistence by updating `config/default.yaml`. The in-memory backend is ephemeral by design.

### Redis connection errors

**Problem**: Redis server not running or wrong URL.

**Solution**:
```bash
# Test connection
redis-cli -u $REDIS_URL ping  # Should return "PONG"

# Check URL format
REDIS_URL=redis://host:port/db  # Correct format
```

### S3 permission errors

**Problem**: IAM credentials don't have bucket access.

**Solution**:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject",
    "s3:DeleteObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::your-bucket-name/*",
    "arn:aws:s3:::your-bucket-name"
  ]
}
```

---

## Further Reading

- [PGVector Documentation](https://github.com/pgvector/pgvector)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Redis Documentation](https://redis.io/docs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
