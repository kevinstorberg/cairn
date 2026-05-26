from abc import ABC, abstractmethod


class BaseJob(ABC):
    name: str

    @abstractmethod
    async def execute(self) -> None: ...
