"""Optional embedding vector search adapter with strict owner scoping."""
from __future__ import annotations

import math
from typing import Any, Callable
from uuid import UUID


class EmbeddingVectorSearch:
    """Rank candidates only after requesting the backing provider for owner-scoped rows."""

    def __init__(self, embed: Callable[[str], list[float]], load_candidates: Callable[..., list[dict[str, Any]]]):
        self.embed, self.load_candidates = embed, load_candidates

    def search(self, *, user_id: str, query: str, limit: int = 10,
               memory_type: str | None = None) -> list[dict[str, Any]]:
        try:
            owner = str(UUID(user_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("user_id must be a valid UUID") from exc
        if not isinstance(query, str) or not query.strip() or not 1 <= limit <= 100:
            raise ValueError("invalid vector search query or limit")
        try:
            query_vector = [float(value) for value in self.embed(query)]
        except (TypeError, ValueError, OverflowError):
            return []
        if not query_vector or any(not math.isfinite(value) for value in query_vector):
            return []
        candidates = self.load_candidates(user_id=owner, memory_type=memory_type)
        allowed = {
            str(item["id"]): item for item in candidates
            if item.get("id") is not None and str(item.get("user_id")) == owner
            and (memory_type is None or item.get("kind") == memory_type)
        }
        qnorm = math.sqrt(sum(value * value for value in query_vector))
        if not qnorm:
            return []
        ranked = []
        for identifier, item in allowed.items():
            try:
                vector = [float(value) for value in item["embedding"]]
                if len(vector) != len(query_vector) or not vector or any(not math.isfinite(value) for value in vector):
                    continue
                norm = math.sqrt(sum(value * value for value in vector))
                if not norm:
                    continue
                score = sum(a * b for a, b in zip(query_vector, vector)) / (qnorm * norm)
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            ranked.append(({**item, "score": score}, score))
        ranked.sort(key=lambda pair: (-pair[1], str(pair[0]["id"])))
        return [item for item, _ in ranked[:limit]]


def create_vector_search(embed: Callable[[str], list[float]] | None = None,
                         load_candidates: Callable[..., list[dict[str, Any]]] | None = None) -> EmbeddingVectorSearch | None:
    if embed is None or load_candidates is None:
        return None
    return EmbeddingVectorSearch(embed, load_candidates)


__all__ = ["EmbeddingVectorSearch", "create_vector_search"]
