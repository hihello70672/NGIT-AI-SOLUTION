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
    def connection(self, user_id=None):
        self.owners.append(user_id)
        yield self.conn


def test_conversation_and_message_writes_bind_authenticated_owner_and_active_parent():
    db = DB([(CONVERSATION, OWNER, "test", "created", "updated")])
    result = MemoryService(db).create_conversation(OWNER, " test ")
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    assert db.conn.calls[0][1] == (OWNER, "test")
    db = DB([("message", OWNER, CONVERSATION, "user", "hello", {}, "created")])
    MemoryService(db).add_message(OWNER, CONVERSATION, "user", "hello")
    sql, params = db.conn.calls[0]
    assert "WHERE id=%s AND user_id=%s AND status='active'" in sql
    assert params[3:5] == (CONVERSATION, OWNER)


def test_cross_owner_message_and_memory_parent_are_rejected():
    db = DB()
    with pytest.raises(LookupError): MemoryService(db).add_message(OWNER, CONVERSATION, "user", "hello")
    with pytest.raises(LookupError): MemoryService(db).save_memory(OWNER, "note", conversation_id=CONVERSATION)
    assert all(call[1][-1] == OWNER for call in db.conn.calls)


def test_reads_are_owner_filtered_for_conversations_messages_and_memories():
    db = DB()
    service = MemoryService(db)
    service.list_conversations(OWNER)
    service.conversation_messages(OWNER, CONVERSATION)
    service.list_memories(OWNER, "fact")
    assert all("user_id=%s" in sql for sql, _ in db.conn.calls)
    assert db.conn.calls[0][1] == (OWNER, 50)
    assert db.conn.calls[1][1] == (OWNER, CONVERSATION, OWNER, 100)
    assert db.conn.calls[2][1] == (OWNER, "fact", 100)


def test_memory_write_and_type_filters_are_owner_bound():
    db = DB([("memory", OWNER, "fact", "note", {}, "created")])
    MemoryService(db).save_memory(OWNER, " note ", "fact")
    assert db.conn.calls[0][1][:3] == (OWNER, "fact", "note")
    db = DB()
    MemoryService(db).list_memories(OWNER, "profile")
    assert db.conn.calls[0][1] == (OWNER, "profile", 100)


def test_search_only_returns_corpus_owned_hits_and_rejects_invalid_inputs():
    class Store:
        def list_memories(self, *args):
            return [{"id": "mine", "user_id": OWNER, "kind": "fact", "content": "cats fish"}]
    class Vector:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [{"id": "mine", "user_id": OWNER, "score": .9},
                    {"id": "foreign", "user_id": OTHER, "score": 1.0}]
    hits = RetrievalService(Store(), Vector()).search(OWNER, "cats fish")
    assert [hit["id"] for hit in hits] == ["mine"] and hits[0]["source"] == "vector"
    with pytest.raises(ValueError): RetrievalService(Store()).search("invalid", "q")
    with pytest.raises(ValueError): RetrievalService(Store()).search(OWNER, "q", limit=0)


def test_embedding_adapter_filters_owner_type_and_non_finite_vectors():
    requests = []
    def loader(**kwargs):
        requests.append(kwargs)
        return [{"id": "mine", "user_id": OWNER, "kind": "fact", "embedding": [1, 0]},
                {"id": "foreign", "user_id": OTHER, "kind": "fact", "embedding": [1, 0]},
                {"id": "bad", "user_id": OWNER, "kind": "fact", "embedding": [math.nan, 0]}]
    adapter = EmbeddingVectorSearch(lambda _: [1, 0], loader)
    hits = adapter.search(user_id=OWNER, query="q", memory_type="fact")
    assert [hit["id"] for hit in hits] == ["mine"]
    assert requests == [{"user_id": OWNER, "memory_type": "fact"}]


def test_source_allowlisting_is_exact_origin_and_does_not_fetch():
    verify = KnowledgeService.verify_source
    allowed = ["https://docs.example.org"]
    assert verify("https://docs.example.org/page", allowed)
    for source in ("https://docs.example.org.attacker.test/page", "https://docs.example.org:444/page",
                   "https://user@docs.example.org/page", "https://docs.example.org/page#frag", "file:///etc/passwd"):
        assert not verify(source, allowed)


def test_verified_ingestion_chunks_and_keeps_source_provenance():
    class Store:
        def __init__(self): self.saved = []
        def save_memory(self, *args):
            self.saved.append(args)
            return {"content": args[1], "metadata": args[-1]}
    store = Store()
    chunks = KnowledgeService(store).ingest_verified(OWNER, "https://docs.example.org/page", "word " * 80,
        ["https://docs.example.org"], chunk_size=100, overlap=10)
    assert len(chunks) > 1 and len(store.saved) == len(chunks)
    assert all(row[-1]["verified_source"] and row[-1]["source"] == "https://docs.example.org/page" for row in store.saved)
    with pytest.raises(PermissionError):
        KnowledgeService(store).ingest_verified(OWNER, "https://evil.test", "private", ["https://docs.example.org"])


def test_optional_vector_adapter_needs_no_provider():
    from services.api.modules.memory.vector import create_vector_search
    assert create_vector_search() is None
