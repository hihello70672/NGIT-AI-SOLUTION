"""Administrative permission and HTTP-boundary regression tests."""
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import AuthContext,AuditLogger,Policy,PolicyEngine,RestrictedActionManager,ApprovalEngine,EmergencyStop,SecurityError
from services.api.modules.admin.service import AdminError,AdminService
from services.api.modules.admin.api import create_admin_router
class FakeDB:
    def __init__(self): self.calls=[]
    def connection(self,caller=None):
        db=self
        class Conn:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def execute(self,sql,params=()):
                db.calls.append((sql,params,caller))
                if "GROUP BY status" in sql:return SimpleNamespace(description=[("status",),("count",)],fetchall=lambda:[("active",3)])
                if "provider_configs WHERE enabled" in sql:return SimpleNamespace(description=[("count",)],fetchall=lambda:[(2,)])
                if "SELECT name FROM roles" in sql or "SELECT name FROM roles" in sql:return SimpleNamespace(description=[("name",)],fetchall=lambda:[(r,) for r in params[0]])
                if "SELECT name FROM roles WHERE name=ANY" in sql:return SimpleNamespace(description=[("name",)],fetchall=lambda:[(r,) for r in params[0]])
                if "UPDATE users" in sql:return SimpleNamespace(fetchone=lambda:("target","t@example.org","Target",params[0],"now"))
                if "SELECT id,email,display_name,status,created_at FROM users WHERE id" in sql:return SimpleNamespace(fetchone=lambda:("target","t@example.org","Target","active","now"))
                if "INSERT INTO admin_rules" in sql or "INSERT INTO service_controls" in sql:return SimpleNamespace(description=[],fetchall=lambda:[])
                return SimpleNamespace(description=[("id",),("email",),("display_name",),("status",),("created_at",)],fetchall=lambda:[])
        return Conn()
def setup_service():
    audit=AuditLogger(); engine=PolicyEngine()
    for name in ("admin.users.read","admin.roles.read","admin.models.read","admin.knowledge.read","admin.learning.read","admin.reports.read","admin.rules.read","admin.audit.read","admin.analytics.read","admin.rules.manage","admin.emergency.engage","admin.emergency.reset"):
        engine.register(Policy(name,frozenset({"admin"})))
    engine.register(Policy("admin.users.manage",frozenset({"admin"}),True,True));engine.register(Policy("admin.services.control",frozenset({"admin"}),True,True))
    approvals=ApprovalEngine(policy_engine=engine);stop=EmergencyStop(audit);actions=RestrictedActionManager(engine,approvals,stop,audit)
    return AdminService(FakeDB(),engine,actions,audit),engine,actions
def test_read_permission_and_db_caller():
    svc,_,_=setup_service()
    with pytest.raises(SecurityError):svc.list_resource(AuthContext("u",frozenset({"user"})),"users")
    assert svc.list_resource(AuthContext("a",frozenset({"admin"})),"users")==[] and svc.database.calls[-1][2]=="a"
def test_restricted_user_change_requires_exact_scope_approval():
    svc,_,actions=setup_service();ctx=AuthContext("a",frozenset({"admin"}))
    with pytest.raises(SecurityError):svc.update_user(ctx,"target",status="disabled")
    grant=actions._approvals.request("requester","admin.users.manage","target");actions._approvals.decide(grant.approval_id,"reviewer",approved=True)
    assert svc.update_user(ctx,"target",status="disabled")["id"]=="target"
    with pytest.raises(SecurityError):svc.update_user(ctx,"different",status="disabled")
def test_rule_and_service_write_validation():
    svc,_,actions=setup_service();ctx=AuthContext("a",frozenset({"admin"}))
    assert svc.create_rule(ctx,"reports.export",["admin"])["action"]=="reports.export"
    with pytest.raises(AdminError):svc.create_rule(ctx,"bad rule",["admin"])
    grant=actions._approvals.request("requester","admin.services.control","api");actions._approvals.decide(grant.approval_id,"reviewer",approved=True)
    assert svc.service_control(ctx,"api",False)=={"service":"api","enabled":False}
def test_analytics_emergency_audit_and_stop():
    svc,_,_=setup_service();ctx=AuthContext("a",frozenset({"admin"}))
    assert svc.analytics(ctx)["enabled_model_providers"]==2
    assert svc.emergency(ctx,True,"incident")=={"stopped":True}
    with pytest.raises(SecurityError):svc.emergency(ctx,True,"again")
    assert svc.audit_events(ctx)
def test_router_rejects_regular_user_and_has_admin_routes():
    svc,_,_=setup_service();app=FastAPI();app.include_router(create_admin_router(svc,lambda:AuthContext("u",frozenset({"user"}))),prefix="/api/v1")
    assert TestClient(app).get("/api/v1/admin/users").status_code==403
    paths={r.path for r in app.routes};assert "/api/v1/admin/analytics/overview" in paths and "/api/v1/admin/emergency" in paths
def test_unknown_action_fails_closed():
    svc,_,_=setup_service()
    with pytest.raises(SecurityError):svc.list_resource(AuthContext("a",frozenset({"admin"})),"unknown")
