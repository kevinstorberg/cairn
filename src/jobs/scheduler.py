import asyncio
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.jobs.base import BaseJob


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
                    asyncio.ensure_future(j.execute())

                return wrapper

            self._scheduler.add_job(_make_wrapper(reg.job), trigger=reg.trigger, id=reg.job.name, **reg.kwargs)
        self._scheduler.start()

    async def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
