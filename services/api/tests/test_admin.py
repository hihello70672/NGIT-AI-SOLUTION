"""Permission boundary tests for the admin service and REST router."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from services.api.security import AuthContext, AuditLogger, Policy, PolicyEngine, RestrictedActionManager, ApprovalEngine, EmergencyStop, SecurityError
from services.api.modules.admin.service import AdminError, AdminService
from services.api.modules.admin.api import create_admin_router


class DB:
    def __init__(self): self.calls = []
    def connection(self, caller=None):
        db = self
        class Ctx:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def execute(self, sql, params=()):
                db.calls.append((sql, params, caller))
                if "provider_configs WHERE enabled" in sql: return SimpleNamespace(description=[("count",)], fetchall=lambda: [(2,)])
                if "GROUP BY status" in sql: return SimpleNamespace(description=[("status",), ("count",)], fetchall=lambda: [("active", 4)])
                if "admin_rules" in sql or "service_controls" in sql: return SimpleNamespace(description=[], fetchall=lambda: [])
                return SimpleNamespace(description=[("id",), ("email",), ("display_name",), ("status",), ("created_at",)], fetchall=lambda: [])
        return Ctx()


def make_service():
    audit = AuditLogger()
    policies = PolicyEngine()
    for name in ("admin.users.read", "admin.roles.read", "admin.models.read", "admin.knowledge.read", "admin.learning.read", "admin.reports.read", "admin.rules.read", "admin.audit.read", "admin.analytics.read"):
        policies.register(Policy(name, frozenset({"admin"})))
    policies.register(Policy("admin.users.manage", frozenset({"admin"}), True, True))
    policies.register(Policy("admin.rules.manage", frozenset({"admin"})))
    policies.register(Policy("admin.services.control", frozenset({"admin"}), True, True))
    policies.register(Policy("admin.emergency.engage", frozenset({"admin"})))
    policies.register(Policy("admin.emergency.reset", frozenset({"admin"})))
    approvals = ApprovalEngine(policy_engine=policies)
    stop = EmergencyStop(audit)
    actions = RestrictedActionManager(policies, approvals, stop, audit)
    return AdminService(DB(), policies, actions, audit), policies, actions


def test_admin_list_requires_server_side_admin_permission():
    service, _, _ = make_service()
    with pytest.raises(SecurityError): service.list_resource(AuthContext("user", frozenset({"user"})), "users")
    assert service.list_resource(AuthContext("root", frozenset({"admin"})), "users") == []


def test_restricted_user_change_requires_exact_approved_scope():
    service, policies, actions = make_service()
    ctx = AuthContext("root", frozenset({"admin"}))
    with pytest.raises(SecurityError): service.update_user(ctx, "target", status="disabled")
    grant = actions._approvals.request("reviewer", "admin.users.manage", "target")
    actions._approvals.decide(grant.approval_id, "reviewer2", approved=True)
    # actor and reviewer separation is enforced; grant was not approved by actor.
    assert service.update_user(ctx, "target", status="disabled")["id"] == "target"


def test_service_control_rule_validation_and_analytics():
    service, _, _ = make_service()
    ctx = AuthContext("root", frozenset({"admin"}))
    assert service.analytics(ctx)["enabled_model_providers"] == 2
    with pytest.raises(SecurityError): service.service_control(ctx, "api", True)
    with pytest.raises(AdminError): service.create_rule(ctx, "bad rule", ["admin"])


def test_emergency_control_and_audit():
    service, _, _ = make_service()
    ctx = AuthContext("root", frozenset({"admin"}))
    assert service.emergency(ctx, True, "incident") == {"stopped": True}
    with pytest.raises(SecurityError): service.emergency(ctx, True, "again")


def test_router_binds_context_from_dependency_and_exposes_admin_endpoints():
    service, _, _ = make_service()
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(create_admin_router(service, lambda: AuthContext("u", frozenset({"user"}))), prefix="/api/v1")
    response = TestClient(app).get("/api/v1/admin/users")
    assert response.status_code == 403
    paths = {route.path for route in app.routes}
    assert "/api/v1/admin/analytics/overview" in paths
    assert "/api/v1/admin/emergency" in paths
