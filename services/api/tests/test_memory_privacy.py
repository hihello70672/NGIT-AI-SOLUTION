"""Privacy regression checks for the private memory services."""

import pytest

from services.api.modules.memory.service import KnowledgeService, MemoryService, RetrievalService

OWNER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"


class Connection:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class Database:
    def __init__(self, rows=()):
        self.conn = Connection(rows)
        self.owners = []

    class Context:
        def __init__(self, db, owner):
            self.db, self.owner = db, owner

        def __enter__(self):
            self.db.owners.append(self.owner)
            return self.db.conn

        def __exit__(self, *args):
            return False

    def connection(self, owner=None):
        return self.Context(self, owner)


def test_retrieval_intersects_vector_hits_with_callers_authorized_corpus():
    class Store:
        def list_memories(self, user_id, *args):
            assert user_id == OWNER
            return [
                {"id": "mine", "user_id": OWNER, "kind": "fact", "content": "cats fish"},
                {"id": "foreign", "user_id": OTHER, "kind": "fact", "content": "cats fish"},
            ]

    class Vector:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [
                {"id": "mine", "user_id": OWNER, "score": .9},
                {"id": "foreign", "user_id": OTHER, "score": 1.0},
            ]

    hits = RetrievalService(Store(), Vector()).search(OWNER, "cats fish")
    assert [hit["id"] for hit in hits] == ["mine"]
    assert all(hit["user_id"] == OWNER for hit in hits)


def test_foreign_vector_hit_cannot_replace_authorized_lexical_result():
    class Store:
        def list_memories(self, user_id, *args):
            return [{"id": "mine", "user_id": OWNER, "kind": "fact", "content": "orchids"}]

    class Vector:
        def search(self, **kwargs):
            return [{"id": "foreign", "user_id": OTHER, "score": 1.0}]

    result = RetrievalService(Store(), Vector()).search(OWNER, "orchids")
    assert [row["id"] for row in result] == ["mine"]


def test_memory_database_access_carries_authenticated_owner():
    db = Database()
    service = MemoryService(db)
    service.list_memories(OWNER)
    sql, params = db.conn.calls[-1]
    assert "WHERE user_id=%s" in sql
    assert params[0] == OWNER
    assert db.owners == [OWNER]


def test_cross_owner_parent_rejected_and_lookup_binds_owner():
    db = Database()
    with pytest.raises(LookupError, match="conversation not found"):
        MemoryService(db).save_memory(OWNER, "private", conversation_id=OTHER)
    sql, params = db.conn.calls[-1]
    assert "id=%s AND user_id=%s" in sql
    assert params[-2:] == (OTHER, OWNER)
    assert db.owners == [OWNER]


def test_malformed_identity_is_rejected_before_database_access():
    db = Database()
    with pytest.raises(ValueError):
        MemoryService(db).list_memories("not-a-uuid")
    assert not db.owners


def test_verified_ingestion_requires_exact_allowlisted_origin_and_no_fetch():
    service = KnowledgeService(MemoryService(Database()))
    allowlist = ["https://kb.example.test"]
    assert service.verify_source("https://kb.example.test/page", allowlist)
    assert not service.verify_source("https://kb.example.test.evil/page", allowlist)
    assert not service.verify_source("https://kb.example.test:444/page", allowlist)
    assert not service.verify_source("file:///etc/passwd", allowlist)
    with pytest.raises(PermissionError, match="source is not verified"):
        service.ingest_verified(OWNER, "https://kb.example.test.evil/page", "untrusted", allowlist)


def test_verified_ingestion_marks_source_and_preserves_owner_provenance():
    class Store:
        def __init__(self):
            self.saved = []

        def save_memory(self, *args):
            self.saved.append(args)
            return {"user_id": args[0], "content": args[1], "metadata": args[-1]}

    store = Store()
    service = KnowledgeService(store)
    docs = service.ingest_verified(OWNER, "https://kb.example.test/page", "orchids " * 80,
                                   ["https://kb.example.test"], chunk_size=100, overlap=10)
    assert len(docs) > 1
    assert len(store.saved) == len(docs)
    assert all(row[0] == OWNER and row[-1]["verified_source"] is True for row in store.saved)
    assert all(row[-1]["source"] == "https://kb.example.test/page" for row in store.saved)
