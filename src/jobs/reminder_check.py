"""Reminder check job - checks for upcoming due dates."""

from datetime import datetime, timedelta

from db.connection import get_session_factory
from db.models.todo import Todo, TodoStatus
from sqlalchemy import select
from src.jobs.base import BaseJob


class ReminderCheckJob(BaseJob):
    """Check for todos with upcoming due dates."""

    name = "reminder_check"

    async def execute(self) -> None:
        """Execute reminder check."""
        print(f"[{datetime.utcnow()}] Running reminder check job...")

        # Query database for todos due in next 24 hours
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        factory = get_session_factory()

        async with factory() as session:
            result = await session.execute(
                select(Todo)
                .where(Todo.status != TodoStatus.COMPLETED)
                .where(Todo.due_date.isnot(None))
                .where(Todo.due_date <= tomorrow)
                .where(Todo.due_date >= now)
            )
            upcoming = result.scalars().all()

        if not upcoming:
            print("No upcoming due dates in next 24 hours.")
            return

        print(f"Found {len(upcoming)} todos with upcoming due dates:")
        for todo in upcoming:
            hours_until_due = (todo.due_date - now).total_seconds() / 3600
            print(f"  - {todo.title} (due in {hours_until_due:.1f} hours)")

        # In a real app, would send notifications here
        # For now, just log the reminders
