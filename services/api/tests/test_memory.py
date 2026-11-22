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


def test_conversation_message_writes_are_owner_bound_and_require_active_conversation():
    db = DB([(CONVERSATION, OWNER, "test", "created", "updated")])
    result = MemoryService(db).create_conversation(OWNER, " test ")
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    assert db.conn.calls[0][1] == (OWNER, "test")
    db = DB([("message-id", OWNER, CONVERSATION, "user", "hello", {}, "created")])
    MemoryService(db).add_message(OWNER, CONVERSATION, "user", "hello")
    assert db.conn.calls[0][1][-2:] == (CONVERSATION, OWNER)
    assert "status='active'" in db.conn.calls[0][0]


def test_message_and_memory_reject_foreign_conversations():
    with pytest.raises(LookupError): MemoryService(DB()).add_message(OWNER, CONVERSATION, "user", "hello")
    with pytest.raises(LookupError): MemoryService(DB()).save_memory(OWNER, "note", conversation_id=CONVERSATION)


def test_reads_and_memory_writes_bind_owner_and_foreign_key():
    db = DB([("mem", OWNER, "fact", "note", {}, "created")])
    MemoryService(db).save_memory(OWNER, " note ")
    assert db.conn.calls[0][1][:3] == (OWNER, "fact", "note")
    db = DB([("mine", OWNER, "fact", "private", {}, "created")])
    assert MemoryService(db).list_memories(OWNER)[0]["user_id"] == OWNER
    assert db.conn.calls[0][1][0] == OWNER and "WHERE user_id=%s" in db.conn.calls[0][0]


def test_message_reads_and_lists_filter_owner():
    db = DB([])
    service = MemoryService(db)
    service.list_conversations(OWNER)
    assert db.conn.calls[-1][1][0] == OWNER
    service.conversation_messages(OWNER, CONVERSATION)
    assert db.conn.calls[-1][1] == (OWNER, CONVERSATION, OWNER, 100)
    assert "c.user_id=%s" in db.conn.calls[-1][0]


def test_invalid_owner_and_limits_are_rejected():
    service = MemoryService(DB())
    with pytest.raises(ValueError): service.list_memories("not-a-uuid")
    with pytest.raises(ValueError): service.list_memories(OWNER, limit=0)
    with pytest.raises(ValueError): service.save_memory(OWNER, "note", "unknown")


def test_lexical_retrieval_returns_only_owner_scoped_memories():
    class Store:
        def list_memories(self, *_): return [{"id": "1", "user_id": OWNER, "kind": "fact", "content": "cats like fish", "metadata": {}}]
    hit = RetrievalService(Store()).search(OWNER, "cats fish")[0]
    assert hit["source"] == "memory" and hit["score"] > 0


def test_vector_hits_cannot_introduce_foreign_or_malformed_records():
    class Store:
        def list_memories(self, *_): return [{"id": "mine", "user_id": OWNER, "kind": "fact", "content": "private", "metadata": {}}]
    class Vector:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [{"id": "mine", "user_id": OWNER, "score": .9}, {"id": "foreign", "user_id": OTHER, "score": 1.0}, {"id": "mine", "user_id": OWNER, "score": math.nan}]
    results = RetrievalService(Store(), Vector()).search(OWNER, "private")
    assert [item["id"] for item in results] == ["mine"] and results[0]["source"] == "vector"


def test_embedding_adapter_filters_owner_kind_and_bad_vectors():
    requests = []
    def loader(**kwargs):
        requests.append(kwargs)
        return [{"id": "mine", "user_id": OWNER, "kind": "fact", "embedding": [1, 0]}, {"id": "foreign", "user_id": OTHER, "kind": "fact", "embedding": [1, 0]}, {"id": "bad", "user_id": OWNER, "kind": "fact", "embedding": [math.nan, 0]}]
    adapter = EmbeddingVectorSearch(lambda _: [1, 0], loader)
    assert [item["id"] for item in adapter.search(user_id=OWNER, query="q")] == ["mine"]
    assert requests == [{"user_id": OWNER, "memory_type": None}]
    with pytest.raises(ValueError): adapter.search(user_id="invalid", query="q")


def test_source_verification_checks_exact_origin_and_never_fetches():
    check = KnowledgeService.verify_source
    assert check("https://docs.example.org/page", ["https://docs.example.org"])
    assert not check("https://docs.example.org.attacker.test/page", ["https://docs.example.org"])
    assert not check("https://docs.example.org:444/page", ["https://docs.example.org"])
    assert not check("https://user@docs.example.org/page", ["https://docs.example.org"])
    assert not check("file:///etc/passwd", ["file:///etc/passwd"])
    assert not check("https://docs.example.org/page#fragment", ["https://docs.example.org"])


def test_ingestion_chunks_and_retains_verified_source_provenance():
    class Store:
        def __init__(self): self.saved = []
        def save_memory(self, *args): self.saved.append(args); return {"content": args[1], "metadata": args[-1]}
    store = Store()
    chunks = KnowledgeService(store).ingest_verified(OWNER, "https://docs.example.org", "word " * 80, ["https://docs.example.org"], chunk_size=100, overlap=10)
    assert len(chunks) > 1 and len(store.saved) == len(chunks)
    assert all(row[-1]["verified_source"] and row[-1]["source"] == "https://docs.example.org" for row in store.saved)
    with pytest.raises(PermissionError): KnowledgeService(store).ingest_verified(OWNER, "https://evil.test", "private", ["https://docs.example.org"])


def test_optional_vector_factory_needs_no_provider():
    from services.api.modules.memory.vector import create_vector_search
    assert create_vector_search() is None


def test_api_sql_uses_established_schema_and_qualified_tables():
    from pathlib import Path
    migration = Path(__file__).parents[1] / "db/migrations/0001_initial_schema.sql"
    schema = migration.read_text()
    for table in ("conversations", "messages", "memories"):
        assert f"ngit.{table}" in schema
    # Database search_path is ngit; service queries preserve established identifiers.
    assert "INSERT INTO memories(user_id,kind,content,metadata)" in Path(__file__).parents[1].joinpath("modules/memory/service.py").read_text()


def test_source_with_credentials_and_non_origin_allowlist_are_rejected():
    verify = KnowledgeService.verify_source
    assert not verify("https://docs.example.org/page", ["https://u:p@docs.example.org"])
    assert not verify("https://docs.example.org/page", ["https://docs.example.org/private"])
