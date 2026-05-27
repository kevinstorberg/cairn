"""Auto-categorization job - categorizes uncategorized todos using graph."""

from datetime import datetime

from langchain_core.messages import HumanMessage

from db.connection import get_session_factory
from db.models.todo import Todo
from sqlalchemy import select
from src.graphs.categorize import build_categorize_graph
from src.jobs.base import BaseJob


class AutoCategorizeJob(BaseJob):
    """Automatically categorize todos without a category using the categorization graph."""

    name = "auto_categorize"

    async def execute(self) -> None:
        """Execute auto-categorization."""
        print(f"[{datetime.utcnow()}] Running auto-categorize job...")

        # Query database for uncategorized todos
        factory = get_session_factory()

        async with factory() as session:
            result = await session.execute(
                select(Todo)
                .where(Todo.category.is_(None))
                .limit(10)  # Process 10 at a time
            )
            uncategorized = result.scalars().all()

        if not uncategorized:
            print("No uncategorized todos found.")
            return

        print(f"Found {len(uncategorized)} uncategorized todos. Processing...")

        # Build categorization graph
        graph = build_categorize_graph()

        # Process each todo
        for todo in uncategorized:
            try:
                todo_text = f"{todo.title}\n{todo.description or ''}"

                initial_state = {
                    "messages": [
                        HumanMessage(
                            content=f"""Categorize this todo: {todo_text}

Use update_todo tool to set category to one of: development, design, documentation, testing, deployment, research, meeting, other"""
                        )
                    ],
                    "todo_id": str(todo.id),
                    "todo_text": todo_text,
                    "category": None,
                }

                # Run graph
                final_state = graph.invoke(initial_state)
                category = final_state.get("category")

                if category:
                    print(f"  ✓ Categorized '{todo.title}' as '{category}'")
                else:
                    print(f"  ✗ Failed to categorize '{todo.title}'")

            except Exception as e:
                print(f"  ✗ Error categorizing '{todo.title}': {e}")

        print("Auto-categorization job complete.")
