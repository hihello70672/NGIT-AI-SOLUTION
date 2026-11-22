from contextlib import contextmanager
import math
import pytest
from services.api.modules.memory.service import KnowledgeService,MemoryService,RetrievalService
OWNER="00000000-0000-0000-0000-000000000001"; OTHER="00000000-0000-0000-0000-000000000002"; CONVERSATION="00000000-0000-0000-0000-000000000009"
class Conn:
    def __init__(self,rows=()):self.rows,self.calls=list(rows),[]
    def execute(self,sql,params=()):self.calls.append((sql,params));return self
    def fetchone(self):return self.rows.pop(0) if self.rows else None
    def fetchall(self):rows,self.rows=self.rows,[];return rows
class DB:
    def __init__(self,rows=()):self.conn,self.owners=Conn(rows),[]
    @contextmanager
    def connection(self,user_id=None):self.owners.append(user_id);yield self.conn
def test_conversation_creation_is_scoped_and_parameterized():
    db=DB([(CONVERSATION,OWNER,"test","active","created","updated")]); result=MemoryService(db).create_conversation(OWNER," test ")
    assert result["user_id"]==OWNER and db.owners==[OWNER]
    sql,params=db.conn.calls[0]; assert "INSERT INTO conversations(user_id,title)" in sql and params==(OWNER,"test")
def test_message_write_requires_active_owned_conversation():
    db=DB()
    with pytest.raises(LookupError):MemoryService(db).add_message(OWNER,CONVERSATION,"user","hi")
    sql,params=db.conn.calls[0];assert "user_id=%s AND status='active'" in sql and params[-2:]==(CONVERSATION,OWNER)
def test_message_reads_join_conversation_and_filter_owner():
    db=DB();MemoryService(db).conversation_messages(OWNER,CONVERSATION)
    sql,params=db.conn.calls[0];assert "JOIN conversations c ON c.user_id=m.user_id" in sql and "m.user_id=%s" in sql and params[:3]==(OWNER,CONVERSATION,OWNER)
def test_memory_type_and_foreign_conversation_rejected():
    service=MemoryService(DB())
    with pytest.raises(ValueError):service.save_memory(OWNER,"x","unknown")
    with pytest.raises(LookupError):service.save_memory(OWNER,"x",conversation_id=CONVERSATION)
    sql,params=service.database.conn.calls[-1];assert "WHERE user_id=%s AND id=%s" in sql and params[-2:]==(OWNER,CONVERSATION)
def test_invalid_owner_and_limits_rejected():
    service=MemoryService(DB())
    with pytest.raises(ValueError):service.list_memories("not-an-id")
    with pytest.raises(ValueError):service.list_memories(OWNER,limit=0)
def test_lexical_and_vector_results_intersect_authorized_corpus():
    docs=[{"id":"mine","user_id":OWNER,"content":"cats like fish","memory_type":"fact"}]
    class M:
        def list_memories(self,*args):return docs
    class V:
        def search(self,**kwargs):return [{"id":"mine","score":.9},{"id":"foreign","score":1.0},{"id":"mine","score":math.nan}]
    hits=RetrievalService(M(),V()).search(OWNER,"cats")
    assert [x["id"] for x in hits]==["mine"] and hits[0]["source"]=="vector"
def test_verified_ingestion_checks_exact_host_port_and_provenance():
    db=DB();service=KnowledgeService(MemoryService(db));allow=["https://docs.example.org"]
    assert service.verify_source("https://docs.example.org/page",allow)
    assert not service.verify_source("https://docs.example.org.attacker.test/page",allow)
    assert not service.verify_source("https://docs.example.org:444/page",allow)
    assert not service.verify_source("https://user@docs.example.org/page",allow)
    with pytest.raises(PermissionError):service.ingest_verified(OWNER,"https://evil.test","private",allow)
    db.conn.rows=[("one",OWNER,None,"summary","chunk one",{"verified_source":True},"now","now"),("two",OWNER,None,"summary","chunk two",{"verified_source":True},"now","now")]
    saved=service.ingest_verified(OWNER,"https://docs.example.org","a "*160,allow,chunk_size=100,overlap=10)
    writes=[c for c in db.conn.calls if "INSERT INTO memory_records" in c[0]]
    assert len(writes)==len(saved)==2 and all('"verified_source":true' in c[1][4] for c in writes)
def test_vector_adapter_discards_foreign_and_nonfinite_embeddings():
    from services.api.modules.memory.vector import EmbeddingVectorSearch
    adapter=EmbeddingVectorSearch(lambda _:[1.,0.],lambda **_:[{"id":"mine","user_id":OWNER,"embedding":[1,0]},{"id":"other","user_id":OTHER,"embedding":[1,0]},{"id":"bad","user_id":OWNER,"embedding":[float("nan"),0]}])
    assert [x["id"] for x in adapter.search(user_id=OWNER,query="hello")] == ["mine"]
    with pytest.raises(ValueError):adapter.search(user_id="invalid",query="hello")
def test_message_query_constrains_owner_and_conversation():
    db=DB();MemoryService(db).conversation_messages(OWNER,CONVERSATION)
    sql,params=db.conn.calls[0]
    assert "c.id=m.conversation_id" in sql and "c.user_id=%s" in sql and params==(OWNER,CONVERSATION,OWNER,100)
def test_empty_allowlist_and_unsafe_url_schemes_fail_closed():
    verifier=KnowledgeService.verify_source
    assert not verifier("https://docs.example.org",[])
    assert not verifier("file:///etc/passwd",["file:///etc/passwd"])
    assert not verifier("https://docs.example.org",["https://user:pass@docs.example.org"])
