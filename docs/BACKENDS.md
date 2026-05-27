# Backend Switching Guide

Cairn supports multiple backends for memory, cache, and storage. Switch between them using environment variables—no code changes required.

## Table of Contents

- [Memory Backends](#memory-backends)
- [Cache Backends](#cache-backends)
- [Storage Backends](#storage-backends)
- [Backend Comparison](#backend-comparison)
- [Migration Guide](#migration-guide)

---

## Memory Backends

Memory backends store vector embeddings for semantic search.

### FAISS (Default - Local)

**Use when**: Development, single-server deployments, prototyping

**Setup**:
```bash
# .env.development
MEMORY_BACKEND=faiss
MEMORY_STORE_PATH=./memory_store
```

**Pros**:
- No external dependencies
- Fast queries
- Simple setup
- Free

**Cons**:
- In-memory only (lost on restart)
- Single-server only
- No persistence to disk by default

**Code example**:
```python
from memory.backends import get_backend

backend = get_backend()  # Returns FAISSBackend
await backend.store("id1", "text", {"key": "value"}, embedding)
results = await backend.search(query_embedding, limit=5)
```

---

### PGVector (PostgreSQL Extension)

**Use when**: Production, need persistence, already using PostgreSQL

**Setup**:
```bash
# Install pgvector extension in PostgreSQL
CREATE EXTENSION vector;

# .env.production
MEMORY_BACKEND=pgvector
DATABASE_URL_PRODUCTION=postgresql+asyncpg://user:pass@host:5432/db
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
- Slower than FAISS for large datasets
- Requires PostgreSQL 11+
- Needs pgvector extension

**Migration from FAISS**:
```python
# 1. Export from FAISS
faiss_backend = get_backend()  # MEMORY_BACKEND=faiss
all_vectors = []  # Manually export vectors

# 2. Switch to pgvector
os.environ["MEMORY_BACKEND"] = "pgvector"
reset_backend()

# 3. Import to pgvector
pgvector_backend = get_backend()
for vector_data in all_vectors:
    await pgvector_backend.store(...)
```

---

### Pinecone (Cloud Vector Database)

**Use when**: Large scale, multi-region, managed service

**Setup**:
```bash
# .env.production
MEMORY_BACKEND=pinecone
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

**Setup**:
```bash
# .env.development
CACHE_BACKEND=memory
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

**Setup**:
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# .env.production
CACHE_BACKEND=redis
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
```bash
# Just change environment variable - no data migration needed
# Cache is ephemeral by nature
CACHE_BACKEND=redis
REDIS_URL=redis://your-redis-server:6379/0
```

---

## Storage Backends

Storage backends handle file uploads (attachments, images, etc.).

### Local Storage (Default)

**Use when**: Development, single-server, small files

**Setup**:
```bash
# .env.development
STORAGE_BACKEND=local
STORAGE_PATH=./storage
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

**Setup**:
```bash
# .env.production
STORAGE_BACKEND=s3
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

---

## Backend Comparison

### Memory Backends

| Feature | FAISS | PGVector | Pinecone |
|---------|-------|----------|----------|
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
- [ ] Export existing FAISS vectors (if any)
- [ ] Set environment variables
- [ ] Install dependencies (`--with pgvector` or `--with pinecone`)
- [ ] Import vectors to new backend
- [ ] Test semantic search

#### Cache
- [ ] Set up Redis server
- [ ] Set `CACHE_BACKEND=redis`
- [ ] Set `REDIS_URL`
- [ ] Install dependency (`--with redis`)
- [ ] No data migration needed (cache is ephemeral)
- [ ] Test cache operations

#### Storage
- [ ] Create S3 bucket
- [ ] Set up IAM credentials
- [ ] Set environment variables
- [ ] Install dependency (`--with aws`)
- [ ] Run migration script to copy files
- [ ] Update application to use S3
- [ ] Test file upload/download

### Environment Variable Reference

```bash
# Development (.env.development)
MEMORY_BACKEND=faiss
MEMORY_STORE_PATH=./memory_store
CACHE_BACKEND=memory
STORAGE_BACKEND=local
STORAGE_PATH=./storage

# Production (.env.production)
MEMORY_BACKEND=pgvector  # or pinecone
DATABASE_URL_PRODUCTION=postgresql+asyncpg://...
CACHE_BACKEND=redis
REDIS_URL=redis://your-redis:6379/0
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=your-bucket
```

---

## Testing with Different Backends

### Test with Memory Cache (Fast)
```bash
CACHE_BACKEND=memory poetry run pytest
```

### Test with Redis (Integration)
```bash
docker run -d -p 6379:6379 redis:7-alpine
CACHE_BACKEND=redis poetry run pytest
```

### Test with FAISS (Default)
```bash
MEMORY_BACKEND=faiss poetry run pytest
```

### Test with Local Storage (Fast)
```bash
STORAGE_BACKEND=local poetry run pytest
```

---

## Troubleshooting

### "Unknown backend" error

**Problem**: Backend name misspelled or not installed.

**Solution**:
```bash
# Check spelling
echo $MEMORY_BACKEND  # Should be: faiss, pgvector, or pinecone

# Install dependencies
poetry install --with pgvector  # or --with pinecone, --with redis, --with aws
```

### Memory backend not persisting data

**Problem**: Using FAISS (in-memory) or not using singleton.

**Solution**: Switch to PGVector or Pinecone for persistence. FAISS is ephemeral by design.

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

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [PGVector Documentation](https://github.com/pgvector/pgvector)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Redis Documentation](https://redis.io/docs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
