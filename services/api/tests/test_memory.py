from contextlib import contextmanager
from uuid import UUID
import pytest
from services.api.modules.memory.service import KnowledgeService, MemoryService, RetrievalService

OWNER = "00000000-0000-0000-0000-000000000001"
OTHER = "00000000-0000-0000-0000-000000000002"

class Conn:
    def __init__(self, rows=()): self.rows, self.calls = list(rows), []
    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self
    def fetchone(self): return self.rows.pop(0) if self.rows else None
    def fetchall(self): return self.rows

class DB:
    def __init__(self, rows=()): self.conn, self.owners = Conn(rows), []
    @contextmanager
    def connection(self, user_id=None):
        self.owners.append(user_id)
        yield self.conn

def test_conversation_creation_scopes_transaction_to_authenticated_owner():
    db=DB([{"id":"conversation","user_id":OWNER,"title":"test","status":"active"}])
    result=MemoryService(db).create_conversation(OWNER," test ")
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    assert "user_id,title" in db.conn.calls[0][0]
    assert db.conn.calls[0][1] == (OWNER,"test")

def test_foreign_conversation_cannot_receive_message():
    db=DB()
    with pytest.raises(LookupError): MemoryService(db).add_message(OWNER, "00000000-0000-0000-0000-000000000009", "user", "hi")
    sql, params=db.conn.calls[0]
    assert "user_id=%s" in sql and params[-2:] == (OWNER, OWNER)
    assert db.owners == [OWNER]

def test_memory_reads_are_owner_filtered_and_scope_rls():
    db=DB([])
    MemoryService(db).list_memories(OWNER)
    sql, params=db.conn.calls[0]
    assert "WHERE user_id=%s" in sql and params[0] == OWNER
    assert db.owners == [OWNER]

def test_invalid_owner_and_type_rejected():
    with pytest.raises(ValueError): MemoryService(DB()).list_memories("not-an-id")
    with pytest.raises(ValueError): MemoryService(DB()).save_memory(OWNER,"x","unknown")

def test_retrieval_falls_back_to_lexical_and_filters_vector_foreign_ids():
    docs=[{"id":"private","user_id":OWNER,"content":"cats like fish","memory_type":"fact"}]
    class Memory:
        def list_memories(self,*args): return docs
    class Vector:
        def search(self,**kwargs):
            assert kwargs["user_id"] == OWNER
            return [{"id":"private","score":0.9},{"id":"foreign","score":1.0}]
    hits=RetrievalService(Memory(),Vector()).search(OWNER,"cats")
    assert [x["id"] for x in hits] == ["private"]
    assert hits[0]["source"] == "vector"
    assert RetrievalService(Memory()).search(OWNER,"fish")[0]["id"] == "private"

def test_verified_source_and_chunked_ingestion_metadata():
    db=DB([{"id":"m1","user_id":OWNER},{"id":"m2","user_id":OWNER}])
    service=KnowledgeService(MemoryService(db))
    assert service.verify_source("https://docs.example.org/page",["https://docs.example.org"])
    assert not service.verify_source("https://docs.example.org.attacker.test/page",["https://docs.example.org"])
    with pytest.raises(PermissionError): service.ingest_verified(OWNER,"https://evil.test", "private data",["https://docs.example.org"])
    results=service.ingest_verified(OWNER,"https://docs.example.org", "a "*150,["https://docs.example.org"],chunk_size=100,overlap=10)
    assert len(results)==2
    assert all("verified_source" in call[1][3] for call in db.conn.calls if "memory_records" in call[0])
