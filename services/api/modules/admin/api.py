"""Authenticated REST endpoints for backend-enforced administration."""
from typing import Any
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from services.api.security import AuthContext
from .service import AdminService
class UserChange(BaseModel):
    status:str|None=None
    roles:list[str]|None=None
class RuleCreate(BaseModel):
    action:str=Field(min_length=1,max_length=127)
    roles:list[str]=Field(min_length=1,max_length=20)
    approval_required:bool=False
    restricted:bool=False
class ServiceChange(BaseModel):enabled:bool
class EmergencyChange(BaseModel):
    engaged:bool
    reason:str=Field(default="",max_length=256)
def create_admin_router(service:AdminService,current_user:Any)->APIRouter:
    router=APIRouter(prefix="/admin",tags=["administration"])
    @router.get("/analytics/overview")
    def analytics(context:AuthContext=Depends(current_user)):return service.analytics(context)
    @router.get("/audit/events")
    def audit_events(limit:int=Query(100,ge=1,le=100),context:AuthContext=Depends(current_user)):return {"items":service.audit_events(context,limit)}
    @router.get("/{kind}")
    def list_resource(kind:str,limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0),q:str=Query("",max_length=100),context:AuthContext=Depends(current_user)):return {"items":service.list_resource(context,kind,limit,offset,q)}
    @router.patch("/users/{user_id}")
    def update_user(user_id:str,body:UserChange,context:AuthContext=Depends(current_user)):return service.update_user(context,user_id,status=body.status,roles=body.roles)
    @router.post("/rules")
    def create_rule(body:RuleCreate,context:AuthContext=Depends(current_user)):return service.create_rule(context,body.action,body.roles,body.approval_required,body.restricted)
    @router.put("/services/{service_name}")
    def control_service(service_name:str,body:ServiceChange,context:AuthContext=Depends(current_user)):return service.service_control(context,service_name,body.enabled)
    @router.post("/emergency")
    def emergency(body:EmergencyChange,context:AuthContext=Depends(current_user)):return service.emergency(context,body.engaged,body.reason)
    return router
__all__=["create_admin_router","UserChange","RuleCreate","ServiceChange","EmergencyChange"]
