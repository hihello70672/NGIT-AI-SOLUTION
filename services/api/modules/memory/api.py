"""Authenticated REST interface for private conversations, memory and knowledge."""
from typing import Any
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from services.api.database import Database
from services.api.security import AuthContext
from services.api.modules.memory.service import KnowledgeService,MemoryService,RetrievalService

def create_router(database:Database,current_user:Any,vector_search:Any|None=None,source_allowlist:tuple[str,...]=())->APIRouter:
    router=APIRouter(tags=["memory"]); memory=MemoryService(database); retrieval=RetrievalService(memory,vector_search); knowledge=KnowledgeService(memory)
    class ConversationInput(BaseModel): title:str=Field(default="New conversation",min_length=1,max_length=240)
    class MessageInput(BaseModel): role:str=Field(min_length=1,max_length=20); content:str=Field(min_length=1,max_length=100000); metadata:dict[str,Any]=Field(default_factory=dict)
    class MemoryInput(BaseModel): content:str=Field(min_length=1,max_length=20000); memory_type:str="fact"; conversation_id:str|None=None; metadata:dict[str,Any]=Field(default_factory=dict)
    class SearchInput(BaseModel): query:str=Field(min_length=1,max_length=2000); limit:int=Field(default=10,ge=1,le=100); memory_type:str|None=None
    class IngestInput(BaseModel): source:str=Field(min_length=1,max_length=1000); text:str=Field(min_length=1,max_length=1000000); conversation_id:str|None=None
    def owner(context:AuthContext=Depends(current_user))->str:return context.user_id
    def invoke(fn,*args,**kwargs):
        try:return fn(*args,**kwargs)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        except LookupError as exc:raise HTTPException(404,"resource not found") from exc
        except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
    @router.post("/conversations",status_code=201)
    def create_conversation(body:ConversationInput,user_id:str=Depends(owner)):return invoke(memory.create_conversation,user_id,body.title)
    @router.get("/conversations")
    def list_conversations(limit:int=50,user_id:str=Depends(owner)):return invoke(memory.list_conversations,user_id,limit)
    @router.get("/conversations/{conversation_id}/messages")
    def messages(conversation_id:str,limit:int=100,user_id:str=Depends(owner)):return invoke(memory.conversation_messages,user_id,conversation_id,limit)
    @router.post("/conversations/{conversation_id}/messages",status_code=201)
    def add_message(conversation_id:str,body:MessageInput,user_id:str=Depends(owner)):return invoke(memory.add_message,user_id,conversation_id,body.role,body.content,body.metadata)
    @router.post("/memories",status_code=201)
    def save_memory(body:MemoryInput,user_id:str=Depends(owner)):return invoke(memory.save_memory,user_id,body.content,body.memory_type,body.conversation_id,body.metadata)
    @router.get("/memories")
    def list_memories(memory_type:str|None=None,limit:int=100,user_id:str=Depends(owner)):return invoke(memory.list_memories,user_id,memory_type,limit)
    @router.post("/memories/search")
    def search(body:SearchInput,user_id:str=Depends(owner)):return invoke(retrieval.search,user_id,body.query,body.limit,body.memory_type)
    @router.post("/knowledge/ingest",status_code=201)
    def ingest(body:IngestInput,user_id:str=Depends(owner)):return invoke(knowledge.ingest_verified,user_id,body.source,body.text,source_allowlist,conversation_id=body.conversation_id)
    return router
