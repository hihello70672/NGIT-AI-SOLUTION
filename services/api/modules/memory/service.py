"""Persistence and retrieval over the established user-scoped schema."""
from __future__ import annotations

import json
import math
import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse
from uuid import UUID

from services.api.database import Database

MEMORY_TYPES = {"profile", "preference", "fact", "summary"}


def _uid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("user_id must be a valid UUID") from exc


class MemoryService:
    """All reads and writes are bound to the authenticated owner."""

    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _dict(row: Any, keys: tuple[str, ...]) -> dict[str, Any]:
        return dict(row) if isinstance(row, Mapping) else dict(zip(keys, row))

    def create_conversation(self, user_id: str, title: str = "New conversation") -> dict[str, Any]:
        owner, title = _uid(user_id), title.strip()
        if not title or len(title) > 240:
            raise ValueError("title must contain 1 to 240 characters")
        keys = ("id", "user_id", "title", "created_at", "updated_at")
        with self.database.connection(owner) as conn:
            row = conn.execute("INSERT INTO conversations(user_id,title) VALUES (%s,%s) RETURNING id,user_id,title,created_at,updated_at", (owner, title)).fetchone()
        return self._dict(row, keys)

    def list_conversations(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        keys = ("id", "user_id", "title", "created_at", "updated_at")
        with self.database.connection(owner) as conn:
            rows = conn.execute("SELECT id,user_id,title,created_at,updated_at FROM conversations WHERE user_id=%s ORDER BY updated_at DESC,id LIMIT %s", (owner, limit)).fetchall()
        return [self._dict(row, keys) for row in rows]

    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        owner, conversation = _uid(user_id), _uid(conversation_id)
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("unsupported message role")
        if not isinstance(content, str) or not content.strip() or len(content) > 100_000:
            raise ValueError("message content must contain 1 to 100000 characters")
        keys = ("id", "user_id", "conversation_id", "role", "content", "metadata", "created_at")
        with self.database.connection(owner) as conn:
            row = conn.execute("INSERT INTO messages(user_id,conversation_id,role,content) SELECT %s,id,%s,%s FROM conversations WHERE id=%s AND user_id=%s AND status='active' RETURNING id,user_id,conversation_id,role,content,'{}'::jsonb AS metadata,created_at", (owner, role, content, conversation, owner)).fetchone()
            if row is None:
                raise LookupError("conversation not found")
            conn.execute("UPDATE conversations SET updated_at=now() WHERE id=%s AND user_id=%s", (conversation, owner))
        return self._dict(row, keys)

    def conversation_messages(self, user_id: str, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        owner, conversation = _uid(user_id), _uid(conversation_id)
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        keys = ("id", "user_id", "conversation_id", "role", "content", "metadata", "created_at")
        with self.database.connection(owner) as conn:
            rows = conn.execute("SELECT m.id,m.user_id,m.conversation_id,m.role,m.content,'{}'::jsonb AS metadata,m.created_at FROM messages m JOIN conversations c ON c.id=m.conversation_id AND c.user_id=m.user_id WHERE m.user_id=%s AND m.conversation_id=%s AND c.user_id=%s ORDER BY m.created_at,m.id LIMIT %s", (owner, conversation, owner, limit)).fetchall()
        return [self._dict(row, keys) for row in rows]

    def save_memory(self, user_id: str, content: str, memory_type: str = "fact", conversation_id: str | None = None, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        owner = _uid(user_id)
        if memory_type not in MEMORY_TYPES:
            raise ValueError("unsupported memory type")
        if not isinstance(content, str) or not content.strip() or len(content) > 20_000:
            raise ValueError("memory content must contain 1 to 20000 characters")
        meta = dict(metadata or {})
        if not all(isinstance(key, str) for key in meta):
            raise ValueError("metadata keys must be strings")
        keys = ("id", "user_id", "kind", "content", "metadata", "created_at")
        with self.database.connection(owner) as conn:
            params: tuple[Any, ...] = (owner, memory_type, content.strip(), json.dumps(meta, separators=(",", ":")))
            if conversation_id is None:
                sql = "INSERT INTO memories(user_id,kind,content,metadata) VALUES (%s,%s,%s,%s::jsonb) RETURNING id,user_id,kind,content,metadata,created_at"
            else:
                conversation = _uid(conversation_id)
                sql = "INSERT INTO memories(user_id,kind,content,metadata) SELECT %s,%s,%s,%s::jsonb FROM conversations WHERE id=%s AND user_id=%s RETURNING id,user_id,kind,content,metadata,created_at"
                params += (conversation, owner)
            row = conn.execute(sql, params).fetchone()
            if row is None:
                raise LookupError("conversation not found")
        return self._dict(row, keys)

    def list_memories(self, user_id: str, memory_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if memory_type is not None and memory_type not in MEMORY_TYPES:
            raise ValueError("unsupported memory type")
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        keys = ("id", "user_id", "kind", "content", "metadata", "created_at")
        with self.database.connection(owner) as conn:
            if memory_type is None:
                rows = conn.execute("SELECT id,user_id,kind,content,metadata,created_at FROM memories WHERE user_id=%s ORDER BY created_at DESC,id LIMIT %s", (owner, limit)).fetchall()
            else:
                rows = conn.execute("SELECT id,user_id,kind,content,metadata,created_at FROM memories WHERE user_id=%s AND kind=%s ORDER BY created_at DESC,id LIMIT %s", (owner, memory_type, limit)).fetchall()
        return [self._dict(row, keys) for row in rows]


class RetrievalService:
    """Lexical retrieval with optional owner/type-filtered vector reranking."""

    def __init__(self, memory: MemoryService, vector_search: Any | None = None):
        self.memory, self.vector_search = memory, vector_search

    @staticmethod
    def _terms(text: str) -> set[str]:
        return set(re.findall(r"[\w'-]+", text.casefold()))

    def search(self, user_id: str, query: str, limit: int = 10, memory_type: str | None = None) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("query must contain 1 to 2000 characters")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        docs = self.memory.list_memories(owner, memory_type, 500)
        terms = self._terms(query)
        ranked: dict[str, dict[str, Any]] = {}
        for doc in docs:
            overlap = terms & self._terms(str(doc["content"]))
            if overlap:
                ranked[str(doc["id"])] = {**doc, "score": len(overlap) / math.sqrt(max(1, len(terms)) * max(1, len(self._terms(str(doc["content"]))))), "source": "memory"}
        if self.vector_search is None:
            return sorted(ranked.values(), key=lambda item: (-item["score"], str(item["id"])))[:limit]
        hits = self.vector_search.search(user_id=owner, query=query, limit=limit, memory_type=memory_type)
        corpus = {str(doc["id"]): doc for doc in docs}
        for hit in hits:
            identifier = str(hit.get("id", ""))
            doc = corpus.get(identifier)
            if doc is None or str(hit.get("user_id", "")) != owner:
                continue
            try:
                score = float(hit.get("score", 0))
            except (ValueError, TypeError):
                continue
            if not math.isfinite(score):
                continue
            if identifier not in ranked or score > ranked[identifier]["score"]:
                ranked[identifier] = {**doc, "score": score, "source": "vector"}
        return sorted(ranked.values(), key=lambda item: (-item["score"], str(item["id"])))[:limit]


class KnowledgeService:
    """Ingest caller-provided text; URL verification never performs network I/O."""

    def __init__(self, memory: MemoryService):
        self.memory = memory

    def ingest_text(self, user_id: str, text: str, source: str, conversation_id: str | None = None, chunk_size: int = 1200, overlap: int = 100) -> list[dict[str, Any]]:
        _uid(user_id)
        if not isinstance(source, str) or not source.strip() or len(source) > 1000:
            raise ValueError("source must contain 1 to 1000 characters")
        if not isinstance(text, str) or not text.strip() or len(text) > 1_000_000:
            raise ValueError("text must contain 1 to 1000000 characters")
        if not isinstance(chunk_size, int) or not 100 <= chunk_size <= 8000 or not isinstance(overlap, int) or not 0 <= overlap < chunk_size:
            raise ValueError("invalid chunking parameters")
        normalized = re.sub(r"\s+", " ", text).strip()
        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            if end < len(normalized):
                boundary = normalized.rfind(" ", start + chunk_size // 2, end)
                if boundary > start:
                    end = boundary
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start = max(start + 1, end - overlap)
        return [self.memory.save_memory(user_id, chunk, "summary", conversation_id, {"source": source.strip(), "chunk_index": i, "verified_source": True}) for i, chunk in enumerate(chunks)]

    @staticmethod
    def verify_source(source: str, allowlist: Sequence[str]) -> bool:
        if not isinstance(source, str) or not source or not allowlist:
            return False
        try:
            candidate = urlparse(source)
            port = candidate.port
        except (ValueError, TypeError):
            return False
        if candidate.scheme not in {"http", "https"} or not candidate.hostname or candidate.username or candidate.password or candidate.fragment:
            return False
        candidate_port = port or (443 if candidate.scheme == "https" else 80)
        for allowed_source in allowlist:
            if not isinstance(allowed_source, str) or not allowed_source:
                continue
            try:
                allowed = urlparse(allowed_source)
                allowed_port = allowed.port
            except (ValueError, TypeError):
                continue
            if allowed.scheme in {"http", "https"} and allowed.hostname and not allowed.username and not allowed.password and not allowed.path.strip("/") and not allowed.query and not allowed.fragment and candidate.scheme == allowed.scheme and candidate.hostname.casefold() == allowed.hostname.casefold() and candidate_port == (allowed_port or (443 if allowed.scheme == "https" else 80)):
                return True
        return False

    def ingest_verified(self, user_id: str, source: str, text: str, allowlist: Sequence[str], **kwargs: Any) -> list[dict[str, Any]]:
        if not self.verify_source(source, allowlist):
            raise PermissionError("source is not verified")
        return self.ingest_text(user_id, text, source, **kwargs)


__all__ = ["MemoryService", "RetrievalService", "KnowledgeService", "MEMORY_TYPES"]
