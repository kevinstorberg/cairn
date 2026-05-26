from typing import Protocol, runtime_checkable


@runtime_checkable
class CheckpointBackend(Protocol):
    async def save(self, thread_id: str, state: dict) -> None: ...
    async def get(self, thread_id: str) -> dict | None: ...
    async def delete(self, thread_id: str) -> None: ...


class InMemoryCheckpointer:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def save(self, thread_id: str, state: dict) -> None:
        self._store[thread_id] = state

    async def get(self, thread_id: str) -> dict | None:
        return self._store.get(thread_id)

    async def delete(self, thread_id: str) -> None:
        self._store.pop(thread_id, None)
