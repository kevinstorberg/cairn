from datetime import datetime
from uuid import UUID

from src.models.base import BaseSchema


class TodoEmbeddingCreate(BaseSchema):
    todo_id: UUID
    embedding: list[float]
    embedding_text: str


class TodoEmbeddingResponse(BaseSchema):
    id: UUID
    todo_id: UUID
    embedding: list[float]
    embedding_text: str
    created_at: datetime
