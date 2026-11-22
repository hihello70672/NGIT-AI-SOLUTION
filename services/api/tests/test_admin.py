"""Regression tests for administration permissions, approvals and routes."""
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import (AuthContext, AuditLogger, Policy, PolicyEngine, RestrictedActionManager,
    ApprovalEngine, EmergencyStop, SecurityError)
from services.api.modules.admin.service import AdminError, AdminService
from services.api.modules.admin.api import create_admin_router

class FakeDB:
    def __init__(self): self.calls=[]
    def connection(self, caller=None):
        db=self
        class Conn:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def execute(self,sql,params=()):
                db.calls.append((sql,params,caller))
                if "GROUP BY status" in sql: return SimpleNamespace(description=[("status",),("count",)],fetchall=lambda:[("active",3)])
                if "provider_configs WHERE enabled" in sql: return SimpleNamespace(description=[("count",)],fetchall=lambda:[(2,)])
                if "SELECT name FROM roles" in sql: return SimpleNamespace(description=[("name",)],fetchall=lambda:[(r,) for r in params[0]])
                if "INSERT INTO admin_rules" in sql or "INSERT INTO service_controls" in sql: return SimpleNamespace(description=[],fetchall=lambda:[])
                return SimpleNamespace(description=[("id",),("email",),("display_name",),("status",),("created_at",)],fetchall=lambda:[])
        return Conn()

def setup_service():
    audit=AuditLogger(); engine=PolicyEngine()
    for name in ("admin.users.read","admin.roles.read","admin.models.read","admin.knowledge.read","admin.learning.read","admin.reports.read","admin.rules.read","admin.audit.read","admin.analytics.read","admin.rules.manage","admin.emergency.engage","admin.emergency.reset"):
        engine.register(Policy(name,frozenset({"admin"})))
    engine.register(Policy("admin.users.manage",frozenset({"admin"}),True,True))
    engine.register(Policy("admin.services.control",frozenset({"admin"}),True,True))
    approvals=ApprovalEngine(policy_engine=engine); stop=EmergencyStop(audit)
    actions=RestrictedActionManager(engine,approvals,stop,audit)
    return AdminService(FakeDB(),engine,actions,audit),engine,actions

def test_read_endpoints_deny_non_admin_and_use_database_caller_identity():
    service,_,_=setup_service()
    with pytest.raises(SecurityError): service.list_resource(AuthContext("u",frozenset({"user"})),"users")
    assert service.list_resource(AuthContext("admin-id",frozenset({"admin"})),"users")==[]
    assert service.database.calls[-1][2]=="admin-id"

def test_restricted_user_update_requires_approval_for_exact_target():
    service,_,actions=setup_service(); ctx=AuthContext("admin-id",frozenset({"admin"}))
    with pytest.raises(SecurityError): service.update_user(ctx,"target",status="disabled")
    grant=actions._approvals.request("reviewer", "admin.users.manage", "target")
    actions._approvals.decide(grant.approval_id,"independent",approved=True)
    assert service.update_user(ctx,"target",status="disabled")["id"]=="target"
    with pytest.raises(SecurityError): service.update_user(ctx,"other",status="disabled")

def test_admin_rule_and_service_writes_are_validated_and_persisted():
    service,_,actions=setup_service(); ctx=AuthContext("admin-id",frozenset({"admin"}))
    assert service.create_rule(ctx,"reports.export",["admin"])["action"]=="reports.export"
    with pytest.raises(AdminError): service.create_rule(ctx,"not allowed",["admin"])
    grant=actions._approvals.request("reviewer","admin.services.control","api")
    actions._approvals.decide(grant.approval_id,"independent",approved=True)
    assert service.service_control(ctx,"api",False)=={"service":"api","enabled":False}
    assert any("INSERT INTO service_controls" in call[0] for call in service.database.calls)

def test_analytics_emergency_stop_and_audit_are_permission_checked():
    service,_,_=setup_service(); ctx=AuthContext("admin-id",frozenset({"admin"}))
    assert service.analytics(ctx)["enabled_model_providers"]==2
    assert service.emergency(ctx,True,"incident")=={"stopped":True}
    with pytest.raises(SecurityError): service.emergency(ctx,True,"duplicate")
    assert service.audit_events(ctx)

def test_router_binds_authenticated_dependency_and_registers_admin_routes():
    service,_,_=setup_service(); app=FastAPI()
    app.include_router(create_admin_router(service,lambda:AuthContext("user-id",frozenset({"user"}))),prefix="/api/v1")
    response=TestClient(app).get("/api/v1/admin/users")
    assert response.status_code==403
    paths={route.path for route in app.routes}
    assert "/api/v1/admin/analytics/overview" in paths
    assert "/api/v1/admin/emergency" in paths

def test_unknown_admin_action_fails_closed():
    service,_,_=setup_service()
    with pytest.raises(SecurityError): service.list_resource(AuthContext("a",frozenset({"admin"})),"unknown")
