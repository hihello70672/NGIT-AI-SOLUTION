"""Optional embedding-based vector search adapter; persistence is supplied externally."""
from __future__ import annotations
import math
from typing import Any, Callable
from uuid import UUID


class EmbeddingVectorSearch:
    """Scores only owner-scoped candidate rows and validates embeddings and outputs."""
    def __init__(self, embed: Callable[[str], list[float]], load_candidates: Callable[..., list[dict[str, Any]]]):
        self.embed, self.load_candidates = embed, load_candidates

    def search(self, *, user_id: str, query: str, limit: int = 10, memory_type: str | None = None) -> list[dict[str, Any]]:
        owner = str(UUID(user_id))
        if not query.strip() or not 1 <= limit <= 100: raise ValueError("invalid vector search query or limit")
        candidates = self.load_candidates(user_id=owner, memory_type=memory_type)
        allowed = {str(item["id"]): item for item in candidates if str(item.get("user_id")) == owner and item.get("id") is not None and (memory_type is None or item.get("memory_type", item.get("kind")) == memory_type)}
        query_vector = self.embed(query)
        if not query_vector or any(not math.isfinite(float(x)) for x in query_vector): return []
        ranked = []
        for identifier, item in allowed.items():
            vector = item.get("embedding")
            if not isinstance(vector, (list, tuple)) or len(vector) != len(query_vector): continue
            try:
                values = [float(x) for x in vector]
                score = sum(a*b for a,b in zip(query_vector, values)) / math.sqrt(sum(a*a for a in query_vector) * sum(b*b for b in values))
            except (ValueError, TypeError, OverflowError, ZeroDivisionError): continue
            if math.isfinite(score): ranked.append(({**item, "id": identifier, "score": score}, score))
        ranked.sort(key=lambda pair: (-pair[1], pair[0]["id"]))
        return [item for item, _ in ranked[:limit]]


def create_vector_search(embed: Callable[[str], list[float]] | None = None, load_candidates: Callable[..., list[dict[str, Any]]] | None = None) -> EmbeddingVectorSearch | None:
    """Avoid constructing an adapter unless both integration callbacks are configured."""
    if embed is None or load_candidates is None: return None
    return EmbeddingVectorSearch(embed, load_candidates)
