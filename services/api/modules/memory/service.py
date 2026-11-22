"""Persistence and retrieval over the established user-scoped schema."""
from __future__ import annotations
import json, math, re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse
from uuid import UUID
from services.api.database import Database
MEMORY_TYPES = {"profile", "preference", "fact", "summary"}
def _uid(value: str) -> str:
    try: return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc: raise ValueError("user_id must be a valid UUID") from exc
class MemoryService:
    """Conversations and memories always use authenticated owner scope."""
    def __init__(self, database: Database): self.database = database
    @staticmethod
    def _dict(row: Any, keys: tuple[str, ...]) -> dict[str, Any]: return dict(row) if isinstance(row, Mapping) else dict(zip(keys, row))
    def create_conversation(self, user_id: str, title: str = "New conversation") -> dict[str, Any]:
        owner, title = _uid(user_id), title.strip()
        if not title or len(title) > 240: raise ValueError("title must contain 1 to 240 characters")
        with self.database.connection(owner) as conn: row = conn.execute("INSERT INTO conversations(user_id,title) VALUES (%s,%s) RETURNING id,user_id,title,status,created_at,updated_at", (owner,title)).fetchone()
        return self._dict(row,("id","user_id","title","status","created_at","updated_at"))
    def list_conversations(self,user_id:str,limit:int=50)->list[dict[str,Any]]:
        owner=_uid(user_id)
        if not 1<=limit<=100: raise ValueError("limit must be between 1 and 100")
        with self.database.connection(owner) as conn: rows=conn.execute("SELECT id,user_id,title,status,created_at,updated_at FROM conversations WHERE user_id=%s ORDER BY updated_at DESC,id LIMIT %s",(owner,limit)).fetchall()
        return [self._dict(r,("id","user_id","title","status","created_at","updated_at")) for r in rows]
    def add_message(self,user_id:str,conversation_id:str,role:str,content:str,metadata:Mapping[str,Any]|None=None)->dict[str,Any]:
        owner,conversation=_uid(user_id),_uid(conversation_id)
        if role not in {"system","user","assistant","tool"}: raise ValueError("unsupported message role")
        if not isinstance(content,str) or not content.strip() or len(content)>100_000: raise ValueError("message content must contain 1 to 100000 characters")
        with self.database.connection(owner) as conn:
            row=conn.execute("INSERT INTO messages(user_id,conversation_id,role,content,metadata) SELECT %s,id,%s,%s,%s::jsonb FROM conversations WHERE id=%s AND user_id=%s AND status='active' RETURNING id,user_id,conversation_id,role,content,metadata,created_at",(owner,role,content,json.dumps(dict(metadata or {}),separators=(",",":")),conversation,owner)).fetchone()
            if row is None: raise LookupError("conversation not found")
            conn.execute("UPDATE conversations SET updated_at=now() WHERE id=%s AND user_id=%s",(conversation,owner))
        return self._dict(row,("id","user_id","conversation_id","role","content","metadata","created_at"))
    def conversation_messages(self,user_id:str,conversation_id:str,limit:int=100)->list[dict[str,Any]]:
        owner,conversation=_uid(user_id),_uid(conversation_id)
        if not 1<=limit<=500: raise ValueError("limit must be between 1 and 500")
        with self.database.connection(owner) as conn: rows=conn.execute("SELECT m.id,m.user_id,m.conversation_id,m.role,m.content,m.metadata,m.created_at FROM messages m JOIN conversations c ON c.user_id=m.user_id AND c.id=m.conversation_id WHERE m.user_id=%s AND m.conversation_id=%s AND c.user_id=%s ORDER BY m.created_at,m.id LIMIT %s",(owner,conversation,owner,limit)).fetchall()
        keys=("id","user_id","conversation_id","role","content","metadata","created_at")
        return [self._dict(r,keys) for r in rows]
    def save_memory(self,user_id:str,content:str,memory_type:str="fact",conversation_id:str|None=None,metadata:Mapping[str,Any]|None=None)->dict[str,Any]:
        owner=_uid(user_id)
        if memory_type not in MEMORY_TYPES: raise ValueError("unsupported memory type")
        if not isinstance(content,str) or not content.strip() or len(content)>20_000: raise ValueError("memory content must contain 1 to 20000 characters")
        meta=json.dumps(dict(metadata or {}),separators=(",",":"))
        with self.database.connection(owner) as conn:
            if conversation_id is None: row=conn.execute("INSERT INTO memory_records(user_id,conversation_id,memory_type,content,metadata) VALUES (%s,NULL,%s,%s,%s::jsonb) RETURNING id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at",(owner,memory_type,content.strip(),meta)).fetchone()
            else:
                conversation=_uid(conversation_id)
                row=conn.execute("INSERT INTO memory_records(user_id,conversation_id,memory_type,content,metadata) SELECT %s,id,%s,%s,%s::jsonb FROM conversations WHERE user_id=%s AND id=%s RETURNING id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at",(owner,memory_type,content.strip(),meta,owner,conversation)).fetchone()
                if row is None: raise LookupError("conversation not found")
        return self._dict(row,("id","user_id","conversation_id","memory_type","content","metadata","created_at","updated_at"))
    def list_memories(self,user_id:str,memory_type:str|None=None,limit:int=100)->list[dict[str,Any]]:
        owner=_uid(user_id)
        if memory_type is not None and memory_type not in MEMORY_TYPES: raise ValueError("unsupported memory type")
        if not 1<=limit<=500: raise ValueError("limit must be between 1 and 500")
        with self.database.connection(owner) as conn:
            if memory_type is None: rows=conn.execute("SELECT id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at FROM memory_records WHERE user_id=%s ORDER BY updated_at DESC,id LIMIT %s",(owner,limit)).fetchall()
            else: rows=conn.execute("SELECT id,user_id,conversation_id,memory_type,content,metadata,created_at,updated_at FROM memory_records WHERE user_id=%s AND memory_type=%s ORDER BY updated_at DESC,id LIMIT %s",(owner,memory_type,limit)).fetchall()
        keys=("id","user_id","conversation_id","memory_type","content","metadata","created_at","updated_at")
        return [self._dict(r,keys) for r in rows]
class RetrievalService:
    """Deterministic lexical search; optional vector hits are intersected with owner corpus."""
    def __init__(self,memory:MemoryService,vector_search:Any|None=None): self.memory,self.vector_search=memory,vector_search
    @staticmethod
    def _terms(text:str)->set[str]: return set(re.findall(r"[\w'-]+",text.casefold()))
    def search(self,user_id:str,query:str,limit:int=10,memory_type:str|None=None)->list[dict[str,Any]]:
        owner=_uid(user_id)
        if not isinstance(query,str) or not query.strip() or len(query)>2000: raise ValueError("query must contain 1 to 2000 characters")
        if not 1<=limit<=100: raise ValueError("limit must be between 1 and 100")
        docs=self.memory.list_memories(owner,memory_type,500); terms=self._terms(query); ranked=[]
        for doc in docs:
            overlap=terms & self._terms(str(doc["content"]))
            if overlap: ranked.append((len(overlap)/math.sqrt(max(1,len(terms))*max(1,len(self._terms(str(doc["content"]))))),doc))
        ranked.sort(key=lambda pair:(-pair[0],str(pair[1]["id"])))
        lexical=[{**doc,"score":score,"source":"memory"} for score,doc in ranked[:limit]]
        if self.vector_search is None: return lexical
        hits=self.vector_search.search(user_id=owner,query=query,limit=limit,memory_type=memory_type); allowed={str(d["id"]):d for d in docs}; merged={str(d["id"]):d for d in lexical}
        for hit in hits:
            identifier=str(hit.get("id",""))
            if identifier not in allowed: continue
            try: score=float(hit.get("score",0))
            except (TypeError,ValueError): continue
            if not math.isfinite(score): continue
            if identifier not in merged or score>merged[identifier]["score"]: merged[identifier]={**allowed[identifier],"score":score,"source":"vector"}
        return sorted(merged.values(),key=lambda d:(-d["score"],str(d["id"])))[:limit]
class KnowledgeService:
    """Ingest caller-provided text only; source verification never fetches network content."""
    def __init__(self,memory:MemoryService): self.memory=memory
    def ingest_text(self,user_id:str,text:str,source:str,conversation_id:str|None=None,chunk_size:int=1200,overlap:int=100)->list[dict[str,Any]]:
        owner=_uid(user_id)
        if not isinstance(source,str) or not source.strip() or len(source)>1000: raise ValueError("source must contain 1 to 1000 characters")
        if not isinstance(text,str) or not text.strip() or len(text)>1_000_000: raise ValueError("text must contain 1 to 1000000 characters")
        if not isinstance(chunk_size,int) or not 100<=chunk_size<=8000 or not isinstance(overlap,int) or not 0<=overlap<chunk_size: raise ValueError("invalid chunking parameters")
        normalized=re.sub(r"\s+"," ",text).strip(); chunks=[]; start=0
        while start<len(normalized):
            end=min(start+chunk_size,len(normalized))
            if end<len(normalized):
                boundary=normalized.rfind(" ",start+chunk_size//2,end)
                if boundary>start: end=boundary
            part=normalized[start:end].strip()
            if part: chunks.append(part)
            if end==len(normalized): break
            start=max(start+1,end-overlap)
        return [self.memory.save_memory(owner,chunk,"summary",conversation_id,{"source":source.strip(),"chunk_index":i,"verified_source":True}) for i,chunk in enumerate(chunks)]
    @staticmethod
    def verify_source(source:str,allowlist:Sequence[str])->bool:
        if not isinstance(source,str) or not source or not allowlist:return False
        try: candidate=urlparse(source); port=candidate.port
        except (ValueError,TypeError): return False
        if candidate.scheme not in {"http","https"} or not candidate.hostname or candidate.username or candidate.password:return False
        for entry in allowlist:
            if not isinstance(entry,str):continue
            if source==entry:return True
            try: allowed=urlparse(entry); allowed_port=allowed.port
            except (ValueError,TypeError):continue
            if allowed.scheme not in {"http","https"} or not allowed.hostname or allowed.username or allowed.password:continue
            cp=port or (443 if candidate.scheme=="https" else 80); ap=allowed_port or (443 if allowed.scheme=="https" else 80)
            if candidate.scheme==allowed.scheme and candidate.hostname.casefold()==allowed.hostname.casefold() and cp==ap:return True
        return False
    def ingest_verified(self,user_id:str,source:str,text:str,allowlist:Sequence[str],**kwargs:Any)->list[dict[str,Any]]:
        if not self.verify_source(source,allowlist):raise PermissionError("source is not verified")
        return self.ingest_text(user_id,text,source,**kwargs)
