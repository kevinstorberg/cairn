from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UUIDMixin


class TodoEmbedding(Base, UUIDMixin):
    __tablename__ = "todo_embeddings"

    todo_id: Mapped[str] = mapped_column(ForeignKey("todos.id", ondelete="CASCADE"), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")

    # Relationships
    todo: Mapped["Todo"] = relationship("Todo", back_populates="embeddings")
