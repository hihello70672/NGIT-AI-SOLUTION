"""Privacy regression checks for memory retrieval and verified ingestion."""

import pytest

from services.api.modules.memory.service import (
    KnowledgeService,
    MemoryService,
    RetrievalService,
)

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

    class _Context:
        def __init__(self, database, owner):
            self.database, self.owner = database, owner

        def __enter__(self):
            self.database.owners.append(self.owner)
            return self.database.conn

        def __exit__(self, *args):
            return False

    def connection(self, owner=None):
        return self._Context(self, owner)


def test_retrieval_does_not_return_foreign_lexical_or_vector_results():
    store = type("Store", (), {"list_memories": lambda self, *args: [
        {"id": "mine", "user_id": OWNER, "kind": "fact", "content": "private cats"},
        {"id": "foreign", "user_id": OTHER, "kind": "fact", "content": "private cats"},
    ]})()

    class Vector:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [
                {"id": "mine", "user_id": OWNER, "score": 0.9},
                {"id": "foreign", "user_id": OTHER, "score": 1.0},
            ]

    hits = RetrievalService(store, Vector()).search(OWNER, "private cats")
    assert [hit["id"] for hit in hits] == ["mine"]
    assert all(hit["user_id"] == OWNER for hit in hits)


def test_vector_failure_cannot_bypass_database_corpus_filter():
    class Store:
        def list_memories(self, user_id, *args):
            assert user_id == OWNER
            return [{"id": "mine", "user_id": OWNER, "kind": "fact", "content": "orchids"}]

    class Vector:
        def search(self, **kwargs):
            return [{"id": "foreign", "user_id": OTHER, "score": 1.0}]

    results = RetrievalService(Store(), Vector()).search(OWNER, "orchids")
    assert [row["id"] for row in results] == ["mine"]


def test_conversation_message_and_memory_queries_bind_owner_and_parent():
    database = Database()
    service = MemoryService(database)
    service.list_conversations(OWNER)
    assert database.conn.calls[-1][1][0] == OWNER
    database.conn.calls.clear()

    # No matching parent must fail closed, and the owner is bound to the lookup.
    with pytest.raises(LookupError):
        service.add_message(OWNER, OTHER, "user", "should not be saved")
    assert all(OWNER in params for _, params in database.conn.calls)
    assert len(database.conn.calls) == 1
    assert "user_id=%s" in database.conn.calls[0][0]


def test_memory_reads_and_writes_are_user_scoped():
    database = Database()
    service = MemoryService(database)
    service.list_memories(OWNER)
    sql, params = database.conn.calls[-1]
    assert "WHERE user_id=%s" in sql
    assert params[0] == OWNER
    assert database.owners == [OWNER]


def test_verified_ingestion_requires_explicit_exact_allowlist_without_network_io():
    knowledge = KnowledgeService(MemoryService(Database()))
    assert knowledge.verify_source("https://kb.example.test/page", ["https://kb.example.test"])
    assert not knowledge.verify_source("https://kb.example.test.evil/page", ["https://kb.example.test"])
    assert not knowledge.verify_source("file:///etc/passwd", ["https://kb.example.test"])
    with pytest.raises(PermissionError):
        knowledge.ingest_verified(OWNER, "https://kb.example.test.evil/page", "untrusted", ["https://kb.example.test"])


def test_foreign_conversation_id_is_not_accepted_for_memory_write():
    database = Database()
    with pytest.raises(LookupError):
        MemoryService(database).save_memory(OWNER, "private", conversation_id=OTHER)
    sql, params = database.conn.calls[-1]
    assert "id=%s AND user_id=%s" in sql
    assert params[-2:] == (OTHER, OWNER)
    assert database.owners == [OWNER]


def test_invalid_user_identity_is_rejected_before_database_access():
    database = Database()
    with pytest.raises(ValueError):
        MemoryService(database).list_memories("not-a-uuid")
    assert database.owners == []


class PermissionError(Exception):
    pass


class LookupError(Exception):
    pass
