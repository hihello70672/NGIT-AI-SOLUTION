from contextlib import contextmanager
import math
import pytest
from services.api.modules.memory.service import KnowledgeService, MemoryService, RetrievalService
OWNER = "00000000-0000-0000-0000-000000000001"
class Conn:
    def __init__(self, rows=()): self.rows, self.calls = list(rows), []
    def execute(self, sql, params=()): self.calls.append((sql, params)); return self
    def fetchone(self): return self.rows.pop(0) if self.rows else None
    def fetchall(self): return self.rows
class DB:
    def __init__(self, rows=()): self.conn, self.owners = Conn(rows), []
    @contextmanager
    def connection(self, user_id=None): self.owners.append(user_id); yield self.conn

def test_conversation_create_and_message_write_are_owner_scoped():
    db=DB([{"id":"conversation","user_id":OWNER,"title":"test","status":"active"}])
    result=MemoryService(db).create_conversation(OWNER," test ")
    assert result["user_id"]==OWNER and db.owners==[OWNER]
    db=DB(); conversation="00000000-0000-0000-0000-000000000009"
    with pytest.raises(LookupError): MemoryService(db).add_message(OWNER,conversation,"user","hi")
    sql,params=db.conn.calls[0]; assert "user_id=%s" in sql and params[-2:]==(conversation,OWNER)

def test_reads_filter_by_owner_and_set_rls_context():
    db=DB(); MemoryService(db).list_memories(OWNER); sql,params=db.conn.calls[0]
    assert "WHERE user_id=%s" in sql and params[0]==OWNER and db.owners==[OWNER]

def test_invalid_owner_and_memory_type_rejected():
    with pytest.raises(ValueError): MemoryService(DB()).list_memories("not-an-id")
    with pytest.raises(ValueError): MemoryService(DB()).save_memory(OWNER,"x","unknown")

def test_retrieval_never_returns_foreign_or_nonfinite_vector_hits():
    docs=[{"id":"private","user_id":OWNER,"content":"cats like fish","memory_type":"fact"}]
    class M:
        def list_memories(self,*args): return docs
    class V:
        def search(self,**kwargs): return [{"id":"private","score":.9},{"id":"foreign","score":1.0},{"id":"private","score":float("nan")}]
    hits=RetrievalService(M(),V()).search(OWNER,"cats")
    assert [x["id"] for x in hits]==["private"] and hits[0]["source"]=="vector"

def test_verified_source_exact_host_port_and_chunk_metadata():
    db=DB([{"id":"m1","user_id":OWNER},{"id":"m2","user_id":OWNER}]); service=KnowledgeService(MemoryService(db))
    assert service.verify_source("https://docs.example.org/page",["https://docs.example.org"])
    assert not service.verify_source("https://docs.example.org.attacker.test/page",["https://docs.example.org"])
    with pytest.raises(PermissionError): service.ingest_verified(OWNER,"https://evil.test","private data",["https://docs.example.org"])
    service.ingest_verified(OWNER,"https://docs.example.org","a "*150,["https://docs.example.org"],chunk_size=100,overlap=10)
    inserts=[c for c in db.conn.calls if "memory_records" in c[0]]
    assert len(inserts)==2 and all('"verified_source":true' in c[1][3] for c in inserts)

def test_embedding_adapter_scopes_candidates_and_cosine_scores():
    from services.api.modules.memory.vector import EmbeddingVectorSearch
    adapter=EmbeddingVectorSearch(lambda text:[1.0,0.0], lambda **kw:[
        {"id":"mine","user_id":OWNER,"content":"ok","embedding":[1,0]},
        {"id":"other","user_id":"other","content":"private","embedding":[1,0]},
        {"id":"bad","user_id":OWNER,"content":"bad","embedding":[float("nan"),0]},
    ])
    hits=adapter.search(user_id=OWNER,query="ok")
    assert [h["id"] for h in hits]==["mine"] and math.isclose(hits[0]["score"],1)
    with pytest.raises(AssertionError):
        EmbeddingVectorSearch(lambda _: [1], lambda **kw: []).search(user_id=OWNER,query="",limit=0)

def test_source_verification_rejects_userinfo_and_invalid_scheme():
    service=KnowledgeService(MemoryService(DB()))
    assert not service.verify_source("https://user@docs.example.org/a",["https://docs.example.org"])
    assert not service.verify_source("file:///etc/passwd",["file:///etc/passwd"])
