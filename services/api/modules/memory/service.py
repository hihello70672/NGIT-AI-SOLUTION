"""Persistence and retrieval over the established user-scoped schema."""
from __future__ import annotations
import json
import math
import re
from typing import Any, Mapping, Sequence
from uuid import UUID
from services.api.database import Database

MEMORY_TYPES = {"profile", "preference", "fact", "summary"}

def _uid(value: str) -> str:
    try: return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc: raise ValueError("user_id must be a valid UUID") from exc

class MemoryService:
    """Conversation and memory operations; every query carries authenticated owner scope."""
    def __init__(self, database: Database): self.database = database
    @staticmethod
    def _conversation(row: Any) -> dict[str, Any]:
        return dict(row) if isinstance(row, Mapping) else dict(zip(("id", "user_id", "title", "status", "created_at", "updated_at"), row))
    def create_conversation(self, user_id: str, title: str = "New conversation") -> dict[str, Any]:
        owner = _uid(user_id); title = title.strip()
        if not title or len(title) > 240: raise ValueError("title must contain 1 to 240 characters")
        with self.database.connection(owner) as conn:
            row = conn.execute("INSERT INTO conversations(user_id,title) VALUES (%s,%s) RETURNING id,user_id,title,status,created_at,updated_at", (owner, title)).fetchone()
        return self._conversation(row)
    def list_conversations(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if not 1 <= limit <= 100: raise ValueError("limit must be between 1 and 100")
        with self.database.connection(owner) as conn: rows = conn.execute("SELECT id,user_id,title,status,created_at,updated_at FROM conversations WHERE user_id=%s ORDER BY updated_at DESC,id LIMIT %s", (owner, limit)).fetchall()
        return [self._conversation(r) for r in rows]
    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        owner, conversation = _uid(user_id), _uid(conversation_id)
        if role not in {"system", "user", "assistant", "tool"}: raise ValueError("unsupported message role")
        if not isinstance(content, str) or not content.strip() or len(content) > 100_000: raise ValueError("message content must contain 1 to 100000 characters")
        safe_metadata = json.dumps(dict(metadata or {}), separators=(",", ":"))
        with self.database.connection(owner) as conn:
            row = conn.execute("INSERT INTO messages(user_id,conversation_id,role,content,metadata) SELECT %s,id,%s,%s,%s::jsonb FROM conversations WHERE id=%s AND user_id=%s AND status='active' RETURNING id,user_id,conversation_id,role,content,metadata,created_at", (owner, role, content, safe_metadata, conversation, owner)).fetchone()
            if row is None: raise LookupError("conversation not found")
            conn.execute("UPDATE conversations SET updated_at=now() WHERE id=%s AND user_id=%s", (conversation, owner))
        return dict(row) if isinstance(row, Mapping) else dict(zip(("id", "user_id", "conversation_id", "role", "content", "metadata", "created_at"), row))
    def conversation_messages(self, user_id: str, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        owner, conversation = _uid(user_id), _uid(conversation_id)
        if not 1 <= limit <= 500: raise ValueError("limit must be between 1 and 500")
        with self.database.connection(owner) as conn: rows = conn.execute("SELECT m.id,m.user_id,m.conversation_id,m.role,m.content,m.metadata,m.created_at FROM messages m JOIN conversations c ON c.user_id=m.user_id AND c.id=m.conversation_id WHERE m.user_id=%s AND m.conversation_id=%s AND c.user_id=%s ORDER BY m.created_at,m.id LIMIT %s", (owner, conversation, owner, limit)).fetchall()
        keys = ("id", "user_id", "conversation_id", "role", "content", "metadata", "created_at")
        return [dict(r) if isinstance(r, Mapping) else dict(zip(keys, r)) for r in rows]
    def save_memory(self, user_id: str, content: str, memory_type: str = "fact", conversation_id: str | None = None, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        owner = _uid(user_id)
        if memory_type not in MEMORY_TYPES: raise ValueError("unsupported memory type")
        if not isinstance(content, str) or not content.strip() or len(content) > 20_000: raise ValueError("memory content must contain 1 to 20000 characters")
        safe_meta = json.dumps(dict(metadata or {}), separators=(",", ":"))
        with self.database.connection(owner) as conn:
            if conversation_id is None:
                row = conn.execute("INSERT INTO memory_records(user_id,conversation_id,memory_type,content,metadata) VALUES (%s,NULL,%s,%s,%s::jsonb) RETURNING id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at", (owner, memory_type, content.strip(), safe_meta)).fetchone()
            else:
                conversation = _uid(conversation_id)
                row = conn.execute("INSERT INTO memory_records(user_id,conversation_id,memory_type,content,metadata) SELECT %s,id,%s,%s,%s::jsonb FROM conversations WHERE user_id=%s AND id=%s RETURNING id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at", (owner, memory_type, content.strip(), safe_meta, owner, conversation)).fetchone()
                if row is None: raise LookupError("conversation not found")
        keys = ("id", "user_id", "conversation_id", "memory_type", "content", "metadata", "created_at", "updated_at")
        return dict(row) if isinstance(row, Mapping) else dict(zip(keys, row))
    def list_memories(self, user_id: str, memory_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if memory_type is not None and memory_type not in MEMORY_TYPES: raise ValueError("unsupported memory type")
        if not 1 <= limit <= 500: raise ValueError("limit must be between 1 and 500")
        with self.database.connection(owner) as conn:
            if memory_type is None: rows = conn.execute("SELECT id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at FROM memory_records WHERE user_id=%s ORDER BY updated_at DESC,id LIMIT %s", (owner, limit)).fetchall()
            else: rows = conn.execute("SELECT id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at FROM memory_records WHERE user_id=%s AND memory_type=%s ORDER BY updated_at DESC,id LIMIT %s", (owner, memory_type, limit)).fetchall()
        keys = ("id", "user_id", "conversation_id", "memory_type", "content", "metadata", "created_at", "updated_at")
        return [dict(r) if isinstance(r, Mapping) else dict(zip(keys, r)) for r in rows]

class RetrievalService:
    """Local lexical retrieval with an optional user-scoped vector scoring adapter."""
    def __init__(self, memory: MemoryService, vector_search: Any | None = None): self.memory, self.vector_search = memory, vector_search
    @staticmethod
    def _terms(text: str) -> set[str]: return set(re.findall(r"[\w'-]+", text.casefold()))
    def search(self, user_id: str, query: str, limit: int = 10, memory_type: str | None = None) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if not isinstance(query, str) or not query.strip() or len(query) > 2000: raise ValueError("query must contain 1 to 2000 characters")
        if not 1 <= limit <= 100: raise ValueError("limit must be between 1 and 100")
        docs = self.memory.list_memories(owner, memory_type, 500); terms = self._terms(query); ranked = []
        for doc in docs:
            overlap = len(terms & self._terms(doc["content"]))
            if overlap: ranked.append((overlap / math.sqrt(max(1, len(self._terms(doc["content"])) * len(terms))), doc))
        ranked.sort(key=lambda item: (-item[0], str(item[1]["id"])))
        lexical = [{**doc, "score": score, "source": "memory"} for score, doc in ranked[:limit]]
        if self.vector_search is None: return lexical
        vector_hits = self.vector_search.search(user_id=owner, query=query, limit=limit, memory_type=memory_type)
        permitted = {str(d["id"]): d for d in docs}; merged = {str(hit["id"]): hit for hit in lexical}
        for hit in vector_hits:
            doc_id = str(hit.get("id", ""))
            if doc_id not in permitted: continue
            score = float(hit.get("score", 0))
            if not math.isfinite(score): continue
            if doc_id not in merged or score > merged[doc_id]["score"]: merged[doc_id] = {**permitted[doc_id], "score": score, "source": "vector"}
        return sorted(merged.values(), key=lambda item: (-item["score"], str(item["id"])))[:limit]

class KnowledgeService:
    """Ingest verified user-provided source text as searchable memory records."""
    def __init__(self, memory: MemoryService): self.memory = memory
    def ingest_text(self, user_id: str, text: str, source: str, conversation_id: str | None = None, chunk_size: int = 1200, overlap: int = 100) -> list[dict[str, Any]]:
        owner = _uid(user_id)
        if not isinstance(source, str) or not source.strip() or len(source) > 1000: raise ValueError("source must contain 1 to 1000 characters")
        if not isinstance(text, str) or not text.strip() or len(text) > 1_000_000: raise ValueError("text must contain 1 to 1000000 characters")
        if not 100 <= chunk_size <= 8000 or not 0 <= overlap < chunk_size: raise ValueError("invalid chunking parameters")
        normalized = re.sub(r"\s+", " ", text).strip(); chunks = []; start = 0
        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            if end < len(normalized):
                boundary = normalized.rfind(" ", start + chunk_size // 2, end)
                if boundary > start: end = boundary
            part = normalized[start:end].strip()
            if part: chunks.append(part)
            if end == len(normalized): break
            start = max(start + 1, end - overlap)
        return [self.memory.save_memory(owner, chunk, "summary", conversation_id, {"source": source.strip(), "chunk_index": i, "verified_source": True}) for i, chunk in enumerate(chunks)]
    @staticmethod
    def verify_source(source: str, allowlist: Sequence[str]) -> bool:
        if not source or not allowlist: return False
        from urllib.parse import urlparse
        candidate = urlparse(source)
        for entry in allowlist:
            allowed = urlparse(entry)
            if candidate.scheme in {"http", "https"} and candidate.hostname and allowed.hostname:
                try:
                    if candidate.scheme == allowed.scheme and candidate.hostname.casefold() == allowed.hostname.casefold() and (candidate.port or (443 if candidate.scheme == "https" else 80)) == (allowed.port or (443 if allowed.scheme == "https" else 80)): return True
                except ValueError: continue
            elif source == entry: return True
        return False
    def ingest_verified(self, user_id: str, source: str, text: str, allowlist: Sequence[str], **kwargs: Any) -> list[dict[str, Any]]:
        if not self.verify_source(source, allowlist): raise PermissionError("source is not verified")
        return self.ingest_text(user_id, text, source, **kwargs)
