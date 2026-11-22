from contextlib import contextmanager
import math
import pytest
from services.api.modules.memory.service import KnowledgeService, MemoryService, RetrievalService

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

def test_conversation_creation_is_scoped_and_parameterized():
    row = (CONVERSATION, OWNER, "test", "active", "created", "updated")
    db = DB([row]); result = MemoryService(db).create_conversation(OWNER, " test ")
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    sql, params = db.conn.calls[0]
    assert "INSERT INTO conversations(user_id,title)" in sql and params == (OWNER, "test")

def test_message_write_requires_active_owned_conversation():
    db = DB(); service = MemoryService(db)
    with pytest.raises(LookupError): service.add_message(OWNER, CONVERSATION, "user", "hi")
    sql, params = db.conn.calls[0]
    assert "c.user_id=%s" in sql and "status='active'" in sql and params[-2:] == (CONVERSATION, OWNER)

def test_message_reads_join_and_constrain_owner():
    db = DB(); MemoryService(db).conversation_messages(OWNER, CONVERSATION)
    sql, params = db.conn.calls[0]
    assert "JOIN conversations c ON c.user_id=m.user_id" in sql and "m.user_id=%s" in sql and params[:3] == (OWNER, CONVERSATION, OWNER)

def test_memory_types_and_foreign_conversation_are_validated():
    service = MemoryService(DB())
    with pytest.raises(ValueError): service.save_memory(OWNER, "x", "unknown")
    with pytest.raises(LookupError): service.save_memory(OWNER, "x", conversation_id=CONVERSATION)
    sql, params = service.database.conn.calls[-1]
    assert "WHERE user_id=%s AND id=%s" in sql and params[-2:] == (OWNER, CONVERSATION)

def test_user_identifier_and_limits_are_validated():
    service = MemoryService(DB())
    with pytest.raises(ValueError): service.list_memories("not-a-uuid")
    with pytest.raises(ValueError): service.list_memories(OWNER, limit=0)

def test_lexical_retrieval_only_returns_owner_records():
    docs = [{"id":"mine", "user_id":OWNER,"content":"cats like fish","memory_type":"fact"}]
    class M:
        def list_memories(self,*args): return docs
    class V:
        def search(self,**kwargs): return [{"id":"mine","score":.9},{"id":"foreign","score":1.0},{"id":"mine","score":math.nan}]
    hits = RetrievalService(M(),V()).search(OWNER,"cats")
    assert [x["id"] for x in hits] == ["mine"] and hits[0]["source"] == "vector"

def test_verified_knowledge_rejects_host_suffix_and_records_chunks():
    db = DB(); service = KnowledgeService(MemoryService(db))
    assert service.verify_source("https://docs.example.org/page", ["https://docs.example.org"])
    assert not service.verify_source("https://docs.example.org.attacker.test/page", ["https://docs.example.org"])
    assert not service.verify_source("https://user@docs.example.org/page", ["https://docs.example.org"])
    with pytest.raises(PermissionError): service.ingest_verified(OWNER,"https://evil.test","private",["https://docs.example.org"])
    db.conn.rows = [("one",OWNER,None,"summary","chunk one",{"verified_source":True},"now","now"),("two",OWNER,None,"summary","chunk two",{"verified_source":True},"now","now")]
    saved = service.ingest_verified(OWNER,"https://docs.example.org","a "*160,["https://docs.example.org"],chunk_size=100,overlap=10)
    writes = [call for call in db.conn.calls if "INSERT INTO memory_records" in call[0]]
    assert len(writes) == len(saved) == 2 and all('"verified_source":true' in call[1][4] for call in writes)

def test_vector_adapter_intersects_owner_corpus_and_checks_scores():
    from services.api.modules.memory.vector import EmbeddingVectorSearch
    adapter = EmbeddingVectorSearch(lambda _: [1.,0.], lambda **_: [
        {"id":"mine","user_id":OWNER,"embedding":[1,0]},
        {"id":"other","user_id":OTHER,"embedding":[1,0]},
        {"id":"invalid","user_id":OWNER,"embedding":[float("nan"),0]},
    ])
    assert [hit["id"] for hit in adapter.search(user_id=OWNER,query="hello")] == ["mine"]
    with pytest.raises(ValueError): adapter.search(user_id="invalid",query="hello")
