"""create todo_embeddings table

Revision ID: 002_create_todo_embeddings
Revises: 001_create_todos
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_create_todo_embeddings"
down_revision: Union[str, None] = "001_create_todos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "todo_embeddings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("todo_id", sa.UUID(), sa.ForeignKey("todos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_todo_embeddings_todo_id"), "todo_embeddings", ["todo_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_todo_embeddings_todo_id"), table_name="todo_embeddings")
    op.drop_table("todo_embeddings")
