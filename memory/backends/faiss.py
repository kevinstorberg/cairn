import numpy as np

from memory.base import MemoryBackend


class FAISSBackend(MemoryBackend):
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._entries: dict[str, dict] = {}
        self._vectors: list[np.ndarray] = []
        self._ids: list[str] = []

    async def store(self, id: str, text: str, metadata: dict, embedding: list[float]) -> None:
        self._entries[id] = {"id": id, "text": text, "metadata": metadata}
        self._vectors.append(np.array(embedding, dtype=np.float32))
        self._ids.append(id)

    async def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict]:
        if not self._vectors:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        scores = []
        for i, vec in enumerate(self._vectors):
            id_ = self._ids[i]
            if id_ not in self._entries:
                continue
            score = float(np.dot(query, vec) / (np.linalg.norm(query) * np.linalg.norm(vec) + 1e-10))
            scores.append((score, id_))

        scores.sort(reverse=True)
        results = []
        for score, id_ in scores[:limit]:
            entry = self._entries[id_]
            results.append({**entry, "score": score})
        return results

    async def delete(self, id: str) -> None:
        self._entries.pop(id, None)
