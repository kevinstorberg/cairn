import pytest

from memory.backends.faiss import FAISSBackend
from memory.base import MemoryBackend


@pytest.mark.unit
class TestFAISSBackend:
    @pytest.fixture
    def backend(self):
        return FAISSBackend(dimension=4)

    async def test_store_and_search(self, backend):
        await backend.store("id1", "hello world", {"tag": "test"}, [1.0, 0.0, 0.0, 0.0])
        results = await backend.search([1.0, 0.0, 0.0, 0.0], limit=1)
        assert len(results) == 1
        assert results[0]["id"] == "id1"
        assert results[0]["text"] == "hello world"

    async def test_search_returns_closest(self, backend):
        await backend.store("id1", "first", {}, [1.0, 0.0, 0.0, 0.0])
        await backend.store("id2", "second", {}, [0.0, 1.0, 0.0, 0.0])
        results = await backend.search([0.9, 0.1, 0.0, 0.0], limit=1)
        assert results[0]["id"] == "id1"

    async def test_delete_removes_entry(self, backend):
        await backend.store("id1", "hello", {}, [1.0, 0.0, 0.0, 0.0])
        await backend.delete("id1")
        results = await backend.search([1.0, 0.0, 0.0, 0.0], limit=10)
        assert all(r["id"] != "id1" for r in results)

    async def test_search_empty_store(self, backend):
        results = await backend.search([1.0, 0.0, 0.0, 0.0], limit=5)
        assert results == []

    async def test_implements_protocol(self, backend):
        assert isinstance(backend, MemoryBackend)
