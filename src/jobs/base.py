from abc import ABC, abstractmethod


class BaseJob(ABC):
    """Base class for scheduled background jobs.

    Subclass and implement execute(). Optionally set timeout_seconds
    to limit execution time (None = no limit).
    """

    name: str
    timeout_seconds: float | None = None

    @abstractmethod
    async def execute(self) -> None: ...
