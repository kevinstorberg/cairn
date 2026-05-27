"""create todos table

Revision ID: 001_create_todos
Revises:
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_create_todos"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", name="todostatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", name="todopriority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("parent_id", sa.UUID(), sa.ForeignKey("todos.id"), nullable=True),
        sa.Column("attachment_key", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_todos_parent_id"), "todos", ["parent_id"], unique=False)
    op.create_index(op.f("ix_todos_status"), "todos", ["status"], unique=False)
    op.create_index(op.f("ix_todos_priority"), "todos", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_todos_priority"), table_name="todos")
    op.drop_index(op.f("ix_todos_status"), table_name="todos")
    op.drop_index(op.f("ix_todos_parent_id"), table_name="todos")
    op.drop_table("todos")
    op.execute("DROP TYPE todopriority")
    op.execute("DROP TYPE todostatus")
