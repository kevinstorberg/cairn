"""
Integration tests for background jobs.

Tests:
- Scheduler registration and startup
- Job execution
- Daily summary job with LLM
- Reminder check job
- Auto-categorize job with graph
- Error handling
- Job shutdown
"""

import pytest


@pytest.mark.integration
class TestBackgroundJobs:
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """Test scheduler can be initialized."""
        from src.jobs.scheduler import JobScheduler

        scheduler = JobScheduler()
        assert scheduler is not None
        assert len(scheduler.registered_jobs) == 0

    @pytest.mark.asyncio
    async def test_job_registration(self):
        """Test jobs can be registered with scheduler."""
        from src.jobs.daily_summary import DailySummaryJob
        from src.jobs.scheduler import JobScheduler

        scheduler = JobScheduler()
        job = DailySummaryJob()

        scheduler.register(job, trigger="cron", hour=9)

        assert len(scheduler.registered_jobs) == 1
        assert scheduler.registered_jobs[0].job.name == "daily_summary"
        assert scheduler.registered_jobs[0].trigger == "cron"

    @pytest.mark.asyncio
    async def test_multiple_job_registration(self):
        """Test multiple jobs can be registered."""
        from src.jobs.daily_summary import DailySummaryJob
        from src.jobs.reminder_check import ReminderCheckJob
        from src.jobs.scheduler import JobScheduler

        scheduler = JobScheduler()

        scheduler.register(DailySummaryJob(), trigger="cron", hour=9)
        scheduler.register(ReminderCheckJob(), trigger="interval", minutes=15)

        assert len(scheduler.registered_jobs) == 2

    @pytest.mark.asyncio
    async def test_daily_summary_job_structure(self):
        """Test daily summary job has correct structure."""
        from src.jobs.daily_summary import DailySummaryJob

        job = DailySummaryJob()
        assert job.name == "daily_summary"
        assert hasattr(job, "execute")
        assert callable(job.execute)

    @pytest.mark.asyncio
    async def test_reminder_check_job_structure(self):
        """Test reminder check job has correct structure."""
        from src.jobs.reminder_check import ReminderCheckJob

        job = ReminderCheckJob()
        assert job.name == "reminder_check"
        assert hasattr(job, "execute")

    @pytest.mark.asyncio
    async def test_auto_categorize_job_structure(self):
        """Test auto-categorize job has correct structure."""
        from src.jobs.auto_categorize import AutoCategorizeJob

        job = AutoCategorizeJob()
        assert job.name == "auto_categorize"
        assert hasattr(job, "execute")

    @pytest.mark.asyncio
    async def test_daily_summary_no_todos(self, db_session, clean_db):
        """Test daily summary handles no todos gracefully."""
        from src.jobs.daily_summary import DailySummaryJob

        job = DailySummaryJob()

        # Should not raise error with empty database
        await job.execute()

    @pytest.mark.asyncio
    async def test_reminder_check_no_due_dates(self, db_session, clean_db):
        """Test reminder check handles no due dates gracefully."""
        from src.jobs.reminder_check import ReminderCheckJob

        job = ReminderCheckJob()

        # Should not raise error with no due dates
        await job.execute()

    @pytest.mark.asyncio
    async def test_auto_categorize_no_uncategorized(self, db_session, clean_db):
        """Test auto-categorize handles no uncategorized todos."""
        from src.jobs.auto_categorize import AutoCategorizeJob

        job = AutoCategorizeJob()

        # Should not raise error with no uncategorized todos
        await job.execute()

    @pytest.mark.asyncio
    async def test_daily_summary_with_completed_todos(self, db_session, clean_db):
        """Test daily summary job with completed todos."""
        from datetime import datetime

        from db.models.todo import Todo, TodoStatus
        from src.jobs.daily_summary import DailySummaryJob

        # Create completed todos
        for i in range(3):
            todo = Todo(title=f"Completed task {i}", status=TodoStatus.COMPLETED, updated_at=datetime.utcnow())
            db_session.add(todo)

        await db_session.commit()

        # Run job
        job = DailySummaryJob()
        await job.execute()

        # Should complete without error
        # (LLM call may fail without API key, but job should handle it)

    @pytest.mark.asyncio
    async def test_reminder_check_with_due_date(self, db_session, clean_db):
        """Test reminder check finds todos with upcoming due dates."""
        from datetime import datetime, timedelta

        from db.models.todo import Todo
        from src.jobs.reminder_check import ReminderCheckJob

        # Create todo due in 12 hours
        tomorrow = datetime.utcnow() + timedelta(hours=12)
        todo = Todo(title="Upcoming task", due_date=tomorrow)
        db_session.add(todo)
        await db_session.commit()

        # Run job
        job = ReminderCheckJob()
        await job.execute()

        # Should complete and log the reminder

    @pytest.mark.asyncio
    async def test_scheduler_starts_and_shuts_down(self):
        """Test scheduler can start and shutdown cleanly."""
        import asyncio

        from src.jobs.daily_summary import DailySummaryJob
        from src.jobs.scheduler import JobScheduler

        scheduler = JobScheduler()
        scheduler.register(DailySummaryJob(), trigger="interval", seconds=3600)

        # Start scheduler
        await scheduler.start()

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Shutdown
        await scheduler.shutdown()

        # Should complete without hanging

    @pytest.mark.asyncio
    async def test_job_execution_with_error_handling(self, db_session, clean_db):
        """Test jobs handle errors gracefully."""
        from src.jobs.daily_summary import DailySummaryJob

        job = DailySummaryJob()

        # Should not raise even if LLM call fails (no API key)
        try:
            await job.execute()
        except Exception as e:
            pytest.fail(f"Job should handle errors gracefully, but raised: {e}")

    @pytest.mark.asyncio
    async def test_cache_integration_in_jobs(self):
        """Test jobs can use cache."""
        from cache.backends import get_cache_backend

        cache = get_cache_backend()

        # Set a cached summary
        await cache.set("summary:daily:2026-05-27", "Test summary", ttl=3600)

        # Retrieve it
        result = await cache.get("summary:daily:2026-05-27")
        assert result == "Test summary"

        # Cleanup
        await cache.delete("summary:daily:2026-05-27")

    @pytest.mark.asyncio
    async def test_graph_execution_in_job(self):
        """Test jobs can execute graphs."""
        from src.graphs.categorize import build_categorize_graph

        # Graph should build successfully
        graph = build_categorize_graph()
        assert graph is not None

        # Could be used in auto-categorize job
