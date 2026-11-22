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

def test_conversation_creation_uses_established_schema_and_authenticated_owner():
    db = DB([(CONVERSATION, OWNER, "test", "created", "updated")])
    result = MemoryService(db).create_conversation(OWNER, " test ")
    sql, params = db.conn.calls[0]
    assert result["user_id"] == OWNER and db.owners == [OWNER]
    assert "INSERT INTO conversations(user_id,title)" in sql and params == (OWNER, "test")

def test_message_write_requires_active_owned_conversation():
    db = DB([])
    with pytest.raises(LookupError): MemoryService(db).add_message(OWNER, CONVERSATION, "user", "hello")
    sql, params = db.conn.calls[0]
    assert "user_id=%s AND status='active'" in sql and params[-2:] == (CONVERSATION, OWNER)

def test_message_reads_use_owner_join_and_parameterized_limits():
    db = DB()
    MemoryService(db).conversation_messages(OWNER, CONVERSATION)
    sql, params = db.conn.calls[0]
    assert "c.user_id=m.user_id" in sql and "m.user_id=%s" in sql and params == (OWNER, CONVERSATION, OWNER, 100)

def test_memories_use_schema_kind_and_reject_foreign_conversation():
    db = DB([]); service = MemoryService(db)
    with pytest.raises(LookupError): service.save_memory(OWNER, "fact", conversation_id=CONVERSATION)
    sql, params = db.conn.calls[0]
    assert "INSERT INTO memories(user_id,kind,content,metadata)" in sql and "WHERE id=%s AND user_id=%s" in sql
    assert params[-2:] == (CONVERSATION, OWNER)
    with pytest.raises(ValueError): service.save_memory(OWNER, "x", "unknown")

def test_memory_listing_cannot_accept_invalid_owner_or_limit():
    service = MemoryService(DB())
    with pytest.raises(ValueError): service.list_memories("not-an-id")
    with pytest.raises(ValueError): service.list_memories(OWNER, limit=0)

def test_lexical_vector_results_intersect_with_owner_memory_corpus():
    docs = [{"id":"mine", "user_id":OWNER, "kind":"fact", "content":"cats like fish"}]
    class M:
        def list_memories(self, *args): return docs
    class V:
        def search(self, **kwargs):
            assert kwargs["user_id"] == OWNER
            return [{"id":"mine", "score":.9}, {"id":"foreign", "score":1}, {"id":"mine", "score":float("nan")}]
    hits = RetrievalService(M(), V()).search(OWNER, "cats")
    assert [hit["id"] for hit in hits] == ["mine"] and hits[0]["source"] == "vector"

def test_source_allowlist_checks_exact_origin_and_ingestion_provenance():
    service = KnowledgeService(MemoryService(DB()))
    allowed = ["https://docs.example.org"]
    assert service.verify_source("https://docs.example.org/page", allowed)
    assert not service.verify_source("https://docs.example.org.attacker.test/page", allowed)
    assert not service.verify_source("https://docs.example.org:444/page", allowed)
    assert not service.verify_source("https://user@docs.example.org/page", allowed)
    assert not service.verify_source("file:///etc/passwd", ["file:///etc/passwd"])
    with pytest.raises(PermissionError): service.ingest_verified(OWNER, "https://evil.test", "private", allowed)

def test_ingest_chunks_text_with_verified_source_metadata_without_fetching():
    class M:
        def __init__(self): self.calls=[]
        def save_memory(self, *args): self.calls.append(args); return {"content":args[1], "metadata":args[-1]}
    memory=M(); service=KnowledgeService(memory)
    saved=service.ingest_verified(OWNER, "https://docs.example.org", "word "*100, ["https://docs.example.org"], chunk_size=100, overlap=10)
    assert len(saved)>1 and len(saved)==len(memory.calls)
    assert all(call[2]=="summary" and call[-1]["verified_source"] for call in memory.calls)
    assert all(call[-1]["source"]=="https://docs.example.org" for call in memory.calls)

def test_vector_adapter_requests_owner_scope_and_discards_cross_user_or_bad_vectors():
    calls=[]
    def load_candidates(**kwargs):
        calls.append(kwargs)
        return [{"id":"mine","user_id":OWNER,"kind":"fact","embedding":[1,0]},
                {"id":"theirs","user_id":OTHER,"kind":"fact","embedding":[1,0]},
                {"id":"bad","user_id":OWNER,"kind":"fact","embedding":[float("nan"),0]}]
    adapter=EmbeddingVectorSearch(lambda _: [1,0],load_candidates)
    assert [x["id"] for x in adapter.search(user_id=OWNER,query="hello")] == ["mine"]
    assert calls == [{"user_id":OWNER,"memory_type":None}]
    with pytest.raises(ValueError): adapter.search(user_id="invalid",query="hello")

@pytest.mark.parametrize("source,allow",[("https://docs.example.org",[]),("https://docs.example.org",["https://user:pass@docs.example.org"]),("https://docs.example.org#frag",["https://docs.example.org"]),("https://docs.example.org",["https://docs.example.org/path"]),("https://docs.example.org",["https://docs.example.org?x=1"])])
def test_source_verification_fails_closed(source, allow):
    assert not KnowledgeService.verify_source(source, allow)
