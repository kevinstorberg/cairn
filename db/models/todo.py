import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDMixin


class TodoStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Todo(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TodoStatus] = mapped_column(
        Enum(TodoStatus, values_callable=lambda x: [e.value for e in x]), default=TodoStatus.PENDING, nullable=False
    )
    priority: Mapped[TodoPriority] = mapped_column(
        Enum(TodoPriority, values_callable=lambda x: [e.value for e in x]), default=TodoPriority.MEDIUM, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("todos.id"), nullable=True)
    attachment_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    subtasks: Mapped[list["Todo"]] = relationship(
        "Todo", back_populates="parent", foreign_keys="[Todo.parent_id]", lazy="select"
    )
    parent: Mapped["Todo | None"] = relationship(
        "Todo", back_populates="subtasks", remote_side="[Todo.id]", lazy="select"
    )
    embeddings: Mapped[list["TodoEmbedding"]] = relationship(
        "TodoEmbedding", back_populates="todo", cascade="all, delete-orphan", lazy="select"
    )
