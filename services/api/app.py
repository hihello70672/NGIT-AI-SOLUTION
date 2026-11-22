"""FastAPI entry point for NGIT identity and modular capability APIs."""
from contextlib import asynccontextmanager
import os
import re
from uuid import uuid4
from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg.errors import UniqueViolation
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from services.api.config import Settings
from services.api.database import Database
from services.api.schemas import RegisterRequest, LoginRequest, UserUpdateRequest, UserResponse, TokenResponse
from services.api.security import SecurityError, create_default_security, AuthContext, Policy
from services.api.services.users import UserService
from services.api.services.auth import AuthService
from services.api.services.tasks import TaskRegistry
from services.api.modules.brain.api import router as brain_router
from services.api.modules.memory.api import create_router as create_memory_router
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, build_agent

settings=Settings.from_env();settings.validate_security_configuration()
db=Database(settings.database_url,settings.database_schema)
authenticator,policies,approvals,audit,emergency,actions=create_default_security()
users=UserService(db);auth=AuthService(users,authenticator);bearer=HTTPBearer(auto_error=False)
tasks=TaskRegistry()

@asynccontextmanager
async def lifespan(_:FastAPI):
    db.open()
    try: yield
    finally: db.close()
app=FastAPI(title="NGIT API",version="1.0.0",lifespan=lifespan)
def request_id(request:Request)->str:return getattr(request.state,"request_id","")

@app.middleware("http")
async def request_id_middleware(request:Request,call_next):
    supplied=request.headers.get("X-Request-ID","")
    safe=supplied if len(supplied)<=128 and re.fullmatch(r"[A-Za-z0-9_.:-]+",supplied) else str(uuid4())
    request.state.request_id=safe;response=await call_next(request);response.headers["X-Request-ID"]=safe;return response

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    fields=[{"field":".".join(map(str,e["loc"][1:])),"message":e["msg"]} for e in exc.errors()]
    return JSONResponse(422,{"error":{"code":"validation_error","message":"Request validation failed","request_id":request_id(request),"details":{"fields":fields}}})
@app.exception_handler(SecurityError)
async def security_error(request:Request,exc:SecurityError):
    status=401 if exc.code=="unauthenticated" else 503 if exc.code=="emergency_stop" else 403
    return JSONResponse(status,{"error":{"code":exc.code,"message":exc.message,"request_id":request_id(request),"details":{}}})
@app.exception_handler(UniqueViolation)
async def unique_error(request:Request,exc:UniqueViolation):return JSONResponse(409,{"error":{"code":"conflict","message":"A resource with these details already exists","request_id":request_id(request),"details":{}}})
@app.exception_handler(ValueError)
async def value_error(request:Request,exc:ValueError):return JSONResponse(422,{"error":{"code":"validation_error","message":str(exc)[:256],"request_id":request_id(request),"details":{}}})
@app.exception_handler(Exception)
async def internal_error(request:Request,exc:Exception):return JSONResponse(500,{"error":{"code":"internal_error","message":"An unexpected error occurred","request_id":request_id(request),"details":{}}})
@app.get("/health",tags=["health"])
def health():return {"status":"ok"}

def public_user(row):
    created=row["created_at"].isoformat() if hasattr(row["created_at"],"isoformat") else row["created_at"]
    return {"id":str(row["id"]),"email":row["email"],"display_name":row["display_name"],"status":row["status"],"roles":list(row.get("roles",[])),"created_at":created}
@app.post(settings.api_prefix+"/auth/register",response_model=TokenResponse,status_code=201,tags=["authentication"])
def register(body:RegisterRequest,request:Request):
    user,token=auth.register(str(body.email),body.password,body.display_name)
    audit.record(action="auth.register",actor_user_id=str(user["id"]),resource_type="user",resource_id=str(user["id"]),request_id=request_id(request))
    return {"access_token":token,"user":public_user(user)}
@app.post(settings.api_prefix+"/auth/login",response_model=TokenResponse,tags=["authentication"])
def login(body:LoginRequest,request:Request):
    user,token=auth.login(str(body.email),body.password)
    audit.record(action="auth.login",actor_user_id=str(user["id"]),resource_type="user",resource_id=str(user["id"]),request_id=request_id(request))
    return {"access_token":token,"user":public_user(user)}
def current_user(credentials:HTTPAuthorizationCredentials|None=Depends(bearer))->AuthContext:
    if credentials is None:raise SecurityError("unauthenticated","Authentication required")
    return auth.authenticate(credentials.credentials)
@app.post(settings.api_prefix+"/auth/logout",status_code=204,tags=["authentication"])
def logout(request:Request,context:AuthContext=Depends(current_user),credentials:HTTPAuthorizationCredentials=Depends(bearer)):
    authenticator.revoke(credentials.credentials);audit.record(action="auth.logout",actor_user_id=context.user_id,resource_type="user",resource_id=context.user_id,request_id=request_id(request));return Response(status_code=204)
@app.get(settings.api_prefix+"/users/me",response_model=UserResponse,tags=["users"])
def get_me(context:AuthContext=Depends(current_user)):
    policies.authorize(context,"profile.read",owner_id=context.user_id);user=users.by_id(context.user_id)
    if user is None:raise SecurityError("unauthenticated","Authentication required")
    return public_user(user)
@app.patch(settings.api_prefix+"/users/me",response_model=UserResponse,tags=["users"])
def update_me(body:UserUpdateRequest,request:Request,context:AuthContext=Depends(current_user)):
    if body.display_name is None:raise ValueError("at least one update field is required")
    policies.authorize(context,"profile.read",owner_id=context.user_id);user=users.update_display_name(context.user_id,body.display_name)
    if user is None:raise SecurityError("unauthenticated","Authentication required")
    audit.record(action="user.profile.updated",actor_user_id=context.user_id,resource_type="user",resource_id=context.user_id,request_id=request_id(request));return public_user(user)
policies.register(Policy("admin.users.manage",frozenset({"admin"})))
@app.get(settings.api_prefix+"/users",tags=["users"])
def list_users(limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0),context:AuthContext=Depends(current_user)):
    policies.authorize(context,"admin.users.manage");return {"users":[public_user(u) for u in users.list_users(limit,offset)],"limit":limit,"offset":offset}
app.include_router(brain_router,prefix=settings.api_prefix,dependencies=[Depends(current_user)])
app.include_router(create_memory_router(db,current_user,source_allowlist=tuple(filter(None,(x.strip() for x in os.getenv("NGIT_KNOWLEDGE_SOURCE_ALLOWLIST","").split(","))))),prefix=settings.api_prefix)
workspace=os.getenv("NGIT_AGENT_WORKSPACE","").strip()
if workspace:
    for name in ("filesystem.write","browser.navigate","computer.perform"):
        policies.register(Policy(f"agent.tool.{name}",frozenset({"user","admin"}),approval_required=True,restricted=True))
    app.include_router(create_agent_router(build_agent(ToolRegistry(),actions,workspace),current_user,approvals,policies),prefix=settings.api_prefix)
__all__=["app"]
