"""Daily summary job - generates summary of completed todos."""

from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage

from cache.backends import get_cache_backend
from db.connection import get_session_factory
from db.models.todo import Todo, TodoStatus
from sqlalchemy import select
from src.agents.llm import build_llm
from src.jobs.base import BaseJob


class DailySummaryJob(BaseJob):
    """Generate daily summary of todos using LLM."""

    name = "daily_summary"

    async def execute(self) -> None:
        """Execute daily summary generation."""
        print(f"[{datetime.utcnow()}] Running daily summary job...")

        # Check cache first
        cache = get_cache_backend()
        today = datetime.utcnow().date().isoformat()
        cache_key = f"summary:daily:{today}"

        try:
            cached = await cache.get(cache_key)
            if cached:
                print(f"Daily summary already generated (cached): {cached[:100]}...")
                return
        except Exception as e:
            print(f"Cache check failed: {e}")

        # Query database for yesterday's completed todos
        yesterday = datetime.utcnow() - timedelta(days=1)
        factory = get_session_factory()

        async with factory() as session:
            # Get completed todos from last 24 hours
            result = await session.execute(
                select(Todo)
                .where(Todo.status == TodoStatus.COMPLETED)
                .where(Todo.updated_at >= yesterday)
                .order_by(Todo.updated_at.desc())
            )
            completed = result.scalars().all()

            # Get pending todos count
            result = await session.execute(
                select(Todo).where(Todo.status == TodoStatus.PENDING)
            )
            pending_count = len(result.scalars().all())

        if not completed and pending_count == 0:
            summary = "No activity in the last 24 hours."
            print(summary)
            return

        # Generate summary with LLM
        completed_list = "\n".join([f"- {todo.title}" for todo in completed[:10]])  # Limit to 10
        prompt = f"""Generate a brief daily summary of completed tasks.

Completed in last 24 hours ({len(completed)} tasks):
{completed_list}

Pending tasks: {pending_count}

Provide a 2-3 sentence summary highlighting accomplishments and what's next."""

        try:
            llm = build_llm(provider="anthropic", model="claude-sonnet-4-6", max_tokens=256)
            response = llm.invoke([HumanMessage(content=prompt)])
            summary = response.content

            print(f"Daily summary generated:\n{summary}")

            # Cache for 24 hours
            await cache.set(cache_key, summary, ttl=86400)

        except Exception as e:
            print(f"LLM summary generation failed: {e}")
            summary = f"Completed {len(completed)} tasks in last 24 hours. {pending_count} tasks pending."
            print(f"Fallback summary: {summary}")
