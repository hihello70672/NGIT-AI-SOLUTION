from contextlib import contextmanager

import math
import pytest
from services.api.modules.memory.service import KnowledgeService, MemoryService, RetrievalService
from services.api.modules.memory.vector import EmbeddingVectorSearch

OWNER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"
CONVERSATION = "00000000-0000-0000-0000-000000000009"


class Conn:
    def __init__(self, rows=()): self.rows, self.calls = list(rows), []
    def execute(self, sql, params=()): self.calls.append((sql, params)); return self
    def fetchone(self): return self.rows.pop(0) if self.rows else None
    def fetchall(self): rows, self.rows = self.rows, []; return rows


class DB:
    def __init__(self, rows=()): self.conn, self.owners = Conn(rows), []
    @contextmanager
    def connection(self, user_id=None): self.owners.append(user_id); yield self.conn


def test_conversation_and_message_writes_are_owner_constrained():
    db = DB([(CONVERSATION, OWNER, "test", "created", "updated")])
    result = MemoryService(db).create_conversation(OWNER, " test ")
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    sql, params = db.conn.calls[0]
    assert "INSERT INTO conversations(user_id,title)" in sql and params == (OWNER, "test")


def test_message_requires_active_owned_conversation():
    db = DB()
    with pytest.raises(LookupError): MemoryService(db).add_message(OWNER, CONVERSATION, "user", "hello")
    sql, params = db.conn.calls[0]
    assert "user_id=%s AND status='active'" in sql and params[-2:] == (CONVERSATION, OWNER)


def test_memory_write_uses_existing_schema_and_validates_foreign_conversation():
    db = DB([("memory-id", OWNER, "fact", "note", {}, "created")])
    result = MemoryService(db).save_memory(OWNER, " note ", "fact")
    sql, params = db.conn.calls[0]
    assert result["kind"] == "fact" and "memories(user_id,kind,content,metadata)" in sql
    assert params[:3] == (OWNER, "fact", "note")
    db = DB()
    with pytest.raises(LookupError): MemoryService(db).save_memory(OWNER, "note", conversation_id=CONVERSATION)
    assert "WHERE id=%s AND user_id=%s" in db.conn.calls[0][0]


def test_read_queries_bind_owner_for_conversation_and_memory():
    db = DB()
    service = MemoryService(db)
    service.list_conversations(OWNER)
    assert "WHERE user_id=%s" in db.conn.calls[-1][0] and db.conn.calls[-1][1][0] == OWNER
    service.conversation_messages(OWNER, CONVERSATION)
    assert "m.user_id=%s" in db.conn.calls[-1][0] and db.conn.calls[-1][1][0] == OWNER
    service.list_memories(OWNER)
    assert "WHERE user_id=%s" in db.conn.calls[-1][0] and db.conn.calls[-1][1][0] == OWNER


def test_invalid_owner_and_limits_are_rejected():
    service = MemoryService(DB())
    with pytest.raises(ValueError): service.list_memories("not-a-uuid")
    with pytest.raises(ValueError): service.list_memories(OWNER, limit=0)


def test_lexical_search_returns_ranked_owner_memory():
    class Store:
        def list_memories(self, *args):
            return [{"id": "1", "user_id": OWNER, "kind": "fact", "content": "cats like fish", "metadata": {}}]
    hits = RetrievalService(Store()).search(OWNER, "cats fish")
    assert hits[0]["id"] == "1" and hits[0]["source"] == "memory" and hits[0]["score"] > 0


def test_vector_retrieval_discards_foreign_and_invalid_provider_hits():
    class Store:
        def list_memories(self, *args):
            return [{"id": "mine", "user_id": OWNER, "kind": "fact", "content": "my private memory"}]
    class Vector:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [{"id": "mine", "user_id": OWNER, "score": .9},
                    {"id": "foreign", "user_id": OTHER, "score": 1.0},
                    {"id": "mine", "user_id": OWNER, "score": math.nan}]
    hits = RetrievalService(Store(), Vector()).search(OWNER, "private")
    assert [item["id"] for item in hits] == ["mine"] and hits[0]["source"] == "vector"


def test_embedding_adapter_filters_owner_kind_and_malformed_vectors():
    candidates = []
    def loader(**kwargs):
        candidates.append(kwargs)
        return [{"id": "mine", "user_id": OWNER, "kind": "fact", "embedding": [1, 0]},
                {"id": "theirs", "user_id": OTHER, "kind": "fact", "embedding": [1, 0]},
                {"id": "bad", "user_id": OWNER, "kind": "fact", "embedding": [math.nan, 0]}]
    adapter = EmbeddingVectorSearch(lambda _: [1, 0], loader)
    assert [item["id"] for item in adapter.search(user_id=OWNER, query="test")] == ["mine"]
    assert candidates == [{"user_id": OWNER, "memory_type": None}]
    with pytest.raises(ValueError): adapter.search(user_id="bad", query="test")


def test_source_allowlist_is_exact_origin_and_never_fetches():
    assert KnowledgeService.verify_source("https://docs.example.org/page", ["https://docs.example.org"])
    assert not KnowledgeService.verify_source("https://docs.example.org.attacker.test/page", ["https://docs.example.org"])
    assert not KnowledgeService.verify_source("https://docs.example.org:444/page", ["https://docs.example.org"])
    assert not KnowledgeService.verify_source("https://user@docs.example.org/page", ["https://docs.example.org"])
    assert not KnowledgeService.verify_source("file:///etc/passwd", ["file:///etc/passwd"])
    assert not KnowledgeService.verify_source("https://docs.example.org/page#fragment", ["https://docs.example.org"])


def test_knowledge_ingestion_chunks_with_source_provenance():
    class Store:
        def __init__(self): self.saved = []
        def save_memory(self, *args): self.saved.append(args); return {"content": args[1], "metadata": args[-1]}
    store = Store()
    service = KnowledgeService(store)
    chunks = service.ingest_verified(OWNER, "https://docs.example.org", "word " * 80,
                                     ["https://docs.example.org"], chunk_size=100, overlap=10)
    assert len(chunks) > 1 and len(store.saved) == len(chunks)
    assert all(args[2] == "summary" and args[-1]["verified_source"] for args in store.saved)
    assert all(args[-1]["source"] == "https://docs.example.org" for args in store.saved)
    with pytest.raises(PermissionError):
        service.ingest_verified(OWNER, "https://evil.test", "private", ["https://docs.example.org"])


def test_optional_vector_search_factory_does_not_require_provider():
    from services.api.modules.memory.vector import create_vector_search
    assert create_vector_search() is None
