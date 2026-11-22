"""Optional embedding-backed vector search adapter; no external service required."""
from __future__ import annotations

import math
from typing import Any, Callable


class EmbeddingVectorSearch:
    """Adapt an embedding function and scoped candidate loader to memory search.

    The adapter intentionally does not own persistence or trust an external
    vector store's tenancy filter. Candidate rows are loaded for the caller's
    authenticated user, and hits are intersected with that corpus before return.
    """

    def __init__(self, embed: Callable[[str], list[float]], load_candidates: Callable[..., list[dict[str, Any]]]):
        self.embed = embed
        self.load_candidates = load_candidates

    def search(self, *, user_id: str, query: str, limit: int = 10, memory_type: str | None = None) -> list[dict[str, Any]]:
        candidates = self.load_candidates(user_id=user_id, memory_type=memory_type)
        allowed = {str(item["id"]): item for item in candidates if str(item.get("user_id")) == str(user_id)}
        query_vector = self.embed(query)
        if not query_vector or any(not math.isfinite(float(x)) for x in query_vector):
            return []
        ranked = []
        for item in candidates:
            identifier = str(item.get("id", ""))
            vector = item.get("embedding")
            if identifier not in allowed or not vector or len(vector) != len(query_vector):
                continue
            try:
                score = sum(float(a) * float(b) for a, b in zip(query_vector, vector))
                norm = math.sqrt(sum(float(x) ** 2 for x in query_vector) * sum(float(x) ** 2 for x in vector))
            except (TypeError, ValueError, OverflowError):
                continue
            if norm and math.isfinite(score / norm):
                ranked.append({**allowed[identifier], "score": score / norm})
        return sorted(ranked, key=lambda hit: (-hit["score"], str(hit["id"])))[:limit]
