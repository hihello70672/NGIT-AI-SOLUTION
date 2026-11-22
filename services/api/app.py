"""FastAPI entry point for NGIT identity and modular API services."""
from contextlib import asynccontextmanager
from uuid import uuid4
import os
from fastapi import FastAPI, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg.errors import UniqueViolation
from services.api.config import Settings
from services.api.database import Database
from services.api.schemas import RegisterRequest, LoginRequest, UserUpdateRequest, UserResponse, TokenResponse
from services.api.security import SecurityError, create_default_security, error_payload, Policy
from services.api.services.users import UserService
from services.api.services.auth import AuthService
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from services.api.modules.brain.api import router as brain_router
from services.api.modules.memory.api import create_router as create_memory_router
from services.api.modules.agent.api import create_router as create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, build_agent

settings = Settings.from_env()
db = Database(settings.database_url, settings.database_schema)
authenticator, policies, approvals, audit, emergency, actions = create_default_security()
users = UserService(db)
auth = AuthService(users, authenticator)
bearer = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.open()
    yield
    db.close()

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None:
        raise SecurityError("unauthenticated", "Authentication required")
    return authenticator.authenticate(credentials.credentials)

app = FastAPI(title="NGIT API", version="1.0.0", lifespan=lifespan)
app.include_router(brain_router, prefix=settings.api_prefix)
app.include_router(create_memory_router(db, current_user), prefix=settings.api_prefix)
_agent_workspace = os.environ.get("NGIT_AGENT_WORKSPACE", "").strip()
if _agent_workspace:
    # Agent capability policies are registered in the shared security engine,
    # not duplicated inside the agent module. Approval is mandatory for each
    # side-effecting capability and is checked against task-step resource IDs.
    for _tool_name in ("filesystem.write", "browser.navigate", "computer.perform"):
        policies.register(Policy(f"agent.tool.{_tool_name}", frozenset({"user", "admin"}),
                                 approval_required=True, restricted=True))
    _agent_tools = ToolRegistry()
    _agent = build_agent(_agent_tools, actions, _agent_workspace)
    app.include_router(create_agent_router(_agent, current_user, approvals), prefix=settings.api_prefix)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = [{"field": ".".join(map(str, e["loc"][1:])), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Request validation failed", "request_id": getattr(request.state, "request_id", None), "details": {"fields": fields}}})

@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError):
    return JSONResponse(status_code=401 if exc.code == "unauthenticated" else 403, content=error_payload(exc, getattr(request.state, "request_id", None)))

@app.exception_handler(UniqueViolation)
async def conflict_handler(request: Request, _: UniqueViolation):
    return JSONResponse(status_code=409, content={"error": {"code": "conflict", "message": "A resource with these details already exists", "request_id": getattr(request.state, "request_id", None), "details": {}}})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": str(exc), "request_id": getattr(request.state, "request_id", None), "details": {}}})

@app.exception_handler(Exception)
async def internal_error_handler(request: Request, _: Exception):
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An unexpected error occurred", "request_id": getattr(request.state, "request_id", None), "details": {}}})

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@app.post(settings.api_prefix + "/auth/register", response_model=TokenResponse, status_code=201, tags=["authentication"])
def register(body: RegisterRequest):
    user, token = auth.register(str(body.email), body.password, body.display_name)
    return {"access_token": token, "user": public_user(user)}

@app.post(settings.api_prefix + "/auth/login", response_model=TokenResponse, tags=["authentication"])
def login(body: LoginRequest):
    user, token = auth.login(str(body.email), body.password)
    return {"access_token": token, "user": public_user(user)}

@app.post(settings.api_prefix + "/auth/logout", status_code=204, tags=["authentication"])
def logout(context=Depends(current_user), credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    authenticator.revoke(credentials.credentials)
    audit.record(action="auth.logout", actor_user_id=context.user_id, resource_type="user", resource_id=context.user_id)
    return Response(status_code=204)

@app.get(settings.api_prefix + "/users/me", response_model=UserResponse, tags=["users"])
def get_me(context=Depends(current_user)):
    user = users.by_id(context.user_id)
    if user is None:
        raise SecurityError("unauthenticated", "Authentication required")
    return public_user(user)

@app.patch(settings.api_prefix + "/users/me", response_model=UserResponse, tags=["users"])
def update_me(body: UserUpdateRequest, context=Depends(current_user)):
    if body.display_name is None:
        raise ValueError("at least one update field is required")
    user = users.update_display_name(context.user_id, body.display_name)
    if user is None:
        raise SecurityError("unauthenticated", "Authentication required")
    audit.record(action="user.profile.updated", actor_user_id=context.user_id, resource_type="user", resource_id=context.user_id)
    return public_user(user)

@app.get(settings.api_prefix + "/admin/users", response_model=list[UserResponse], tags=["users"])
def admin_users(context=Depends(current_user)):
    actions.authorize(context, "admin.users.manage", "users")
    with db.connection(context.user_id) as conn:
        rows = conn.execute("SELECT u.id,u.email,u.display_name,u.status,u.created_at,COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::text[]) AS roles FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id GROUP BY u.id ORDER BY u.created_at DESC LIMIT 100").fetchall()
    return [public_user(dict(row)) for row in rows]

@app.get(settings.api_prefix + "/admin/audit", tags=["admin"])
def admin_audit(context=Depends(current_user)):
    actions.authorize(context, "admin.users.manage", "audit_logs")
    return list(audit.events())

def public_user(row):
    created_at = row["created_at"]
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    return {"id": str(row["id"]), "email": row["email"], "display_name": row["display_name"], "status": row["status"], "roles": list(row.get("roles", [])), "created_at": created_at}
