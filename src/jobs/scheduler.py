import asyncio
import logging
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.jobs.base import BaseJob

logger = logging.getLogger(__name__)


@dataclass
class RegisteredJob:
    job: BaseJob
    trigger: str
    kwargs: dict


class JobScheduler:
    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._registered_jobs: list[RegisteredJob] = []

    @property
    def registered_jobs(self) -> list[RegisteredJob]:
        return self._registered_jobs

    def register(self, job: BaseJob, *, trigger: str = "interval", **kwargs) -> None:
        self._registered_jobs.append(RegisteredJob(job=job, trigger=trigger, kwargs=kwargs))

    async def start(self) -> None:
        for reg in self._registered_jobs:

            def _make_wrapper(j: BaseJob):
                def wrapper():
                    asyncio.ensure_future(self._safe_execute(j))

                return wrapper

            self._scheduler.add_job(_make_wrapper(reg.job), trigger=reg.trigger, id=reg.job.name, **reg.kwargs)
        self._scheduler.start()

    async def _safe_execute(self, job: BaseJob) -> None:
        """Execute a job with error handling and optional timeout."""
        try:
            timeout = getattr(job, "timeout_seconds", None)
            if timeout:
                await asyncio.wait_for(job.execute(), timeout=timeout)
            else:
                await job.execute()
        except asyncio.TimeoutError:
            logger.error(f"Job '{job.name}' timed out after {job.timeout_seconds}s")
        except Exception:
            logger.exception(f"Job '{job.name}' failed")

    async def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
