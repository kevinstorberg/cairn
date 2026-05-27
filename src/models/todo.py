from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from src.models.base import BaseSchema


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TodoCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: datetime | None = None
    category: str | None = Field(None, max_length=100)
    parent_id: UUID | None = None


class TodoUpdate(BaseSchema):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: TodoStatus | None = None
    priority: TodoPriority | None = None
    due_date: datetime | None = None
    category: str | None = Field(None, max_length=100)


class TodoResponse(BaseSchema):
    id: UUID
    title: str
    description: str | None
    status: TodoStatus
    priority: TodoPriority
    due_date: datetime | None
    category: str | None
    parent_id: UUID | None
    attachment_key: str | None
    created_at: datetime
    updated_at: datetime
