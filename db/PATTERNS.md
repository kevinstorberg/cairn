# Database Patterns for Cairn

This document covers common database patterns and pitfalls discovered during template testing.

## PostgreSQL ARRAY Types

**Problem**: Using Python `float` in `ARRAY()` causes runtime errors.

**Wrong**:
```python
from sqlalchemy.dialects.postgresql import ARRAY

embedding: Mapped[list[float]] = mapped_column(ARRAY(float))  # ❌ WRONG
```

**Correct**:
```python
from sqlalchemy import Float
from sqlalchemy.dialects.postgresql import ARRAY

embedding: Mapped[list[float]] = mapped_column(ARRAY(Float))  # ✅ CORRECT
```

**Rule**: Always use SQLAlchemy types (`Float`, `String`, `Integer`) inside `ARRAY()`, never Python primitives.

**Why**: SQLAlchemy needs type objects that can be compiled to SQL. Python's `float` is not a SQLAlchemy type.

---

## Self-Referential Relationships

**Problem**: Parent/child relationships without explicit configuration cause "ambiguous foreign keys" errors.

**Solution**: Always specify `foreign_keys` and `remote_side`:

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Todo(Base):
    __tablename__ = "todos"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("todos.id"), nullable=True)
    
    # Parent → Children relationship
    subtasks: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="parent",
        foreign_keys="[Todo.parent_id]",  # ✅ Explicit
        lazy="select"
    )
    
    # Child → Parent relationship  
    parent: Mapped["Todo | None"] = relationship(
        "Todo",
        back_populates="subtasks",
        remote_side="[Todo.id]",  # ✅ Explicit
        lazy="select"
    )
```

**Why**: SQLAlchemy can't automatically determine which side is the parent and which is the child in self-referential relationships. Explicit configuration removes ambiguity.

---

## Enum Type Declarations

**Problem**: Enum values stored as names (`"PENDING"`) instead of values (`"pending"`) in database.

**Solution**: Use `values_callable`:

```python
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Todo(Base):
    __tablename__ = "todos"
    
    # Correct enum declaration
    status: Mapped[TodoStatus] = mapped_column(
        SQLEnum(TodoStatus, values_callable=lambda x: [e.value for e in x]),  # ✅ Store values
        nullable=False,
        default=TodoStatus.PENDING
    )
```

**Why**: Without `values_callable`, SQLAlchemy stores enum names (`PENDING`) instead of their values (`pending`). This causes mismatches between your Python code and database values.

**Alternative**: If you want to store names instead of values, use `Enum(TodoStatus, native_enum=False)` but this is less common.

---

## Async Relationship Loading

**Problem**: Accessing relationships in async code causes "greenlet" errors.

**Solution**: Use eager loading or `selectinload`:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Wrong - lazy loading in async context
async def get_todo_with_subtasks(session, todo_id):
    result = await session.execute(select(Todo).where(Todo.id == todo_id))
    todo = result.scalar_one()
    subtasks = todo.subtasks  # ❌ Causes greenlet error

# Correct - eager loading
async def get_todo_with_subtasks(session, todo_id):
    result = await session.execute(
        select(Todo)
        .where(Todo.id == todo_id)
        .options(selectinload(Todo.subtasks))  # ✅ Eager load
    )
    todo = result.scalar_one()
    subtasks = todo.subtasks  # Works!
```

**Why**: SQLAlchemy's async mode doesn't support lazy loading. Relationships must be explicitly loaded in the same query.

---

## Timestamp Mixins

**Pattern**: Create a mixin for automatic timestamps:

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class Todo(Base, TimestampMixin):
    __tablename__ = "todos"
    # Automatically gets created_at and updated_at
```

**Why**: DRY principle - define once, use everywhere.

---

## UUID Primary Keys

**Pattern**: Use UUIDs for distributed systems:

```python
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class UUIDMixin:
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

class Todo(Base, UUIDMixin):
    __tablename__ = "todos"
    # Automatically gets UUID primary key
```

**Why**: UUIDs prevent ID conflicts in distributed systems and allow client-side ID generation.

---

## Connection Pooling in Tests

**Problem**: Tests fail with "operation in progress" errors.

**Solution**: Use `NullPool` in test fixtures:

```python
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture
def test_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://localhost:5432/cairn_test",
        poolclass=NullPool  # ✅ No pooling in tests
    )
    yield engine
    engine.sync_engine.dispose()
```

**Why**: Connection pooling can cause conflicts when multiple test fixtures create separate engines. `NullPool` creates a fresh connection for each query.

---

## Further Reading

- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL ARRAY Types](https://www.postgresql.org/docs/current/arrays.html)
- [Self-Referential Relationships](https://docs.sqlalchemy.org/en/20/orm/self_referential.html)
