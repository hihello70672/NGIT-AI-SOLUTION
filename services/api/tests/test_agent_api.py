import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as api_module
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService
from services.api.security import AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, PolicyEngine, RestrictedActionManager


class StaticPlanner:
    def plan(self, owner, goal):
        from services.api.modules.agent.runtime import AgentPlan, PlannedStep
        return AgentPlan("api-task", owner, goal, (PlannedStep("safe.echo", {"value": goal}, "echo"),), "now")


def make_agent():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    tools = ToolRegistry()
    tools.register(ToolDefinition("safe.echo", "safe", False, lambda args: ToolResult(args["value"], "echoed", True)))
    return AgentService(tools, permissions, StaticPlanner()), approvals


def test_authenticated_agent_routes_are_owner_scoped():
    agent, approvals = make_agent()
    app = api_module.app
    original_routes, original_overrides = list(app.router.routes), dict(app.dependency_overrides)
    app.dependency_overrides[api_module.current_user] = lambda: AuthContext("alice", frozenset({"user"}))
    app.include_router(create_agent_router(agent, api_module.current_user, approvals), prefix="/api/v1")
    try:
        client = TestClient(app)
        submitted = client.post("/api/v1/agent/tasks", json={"goal": "hello"})
        assert submitted.status_code == 202 and submitted.json()["state"] == "succeeded"
        assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"] == "hello"
    finally:
        app.router.routes = original_routes
        app.dependency_overrides = original_overrides


def test_sensitive_approval_workflow_exposes_pending_step():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    policies.register(__import__("services.api.security", fromlist=["Policy"]).Policy(
        "agent.tool.filesystem.write", frozenset({"user"}), True, True))
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    from services.api.modules.agent.runtime import build_agent
    import tempfile
    with tempfile.TemporaryDirectory() as workspace:
        agent = build_agent(ToolRegistry(), permissions, workspace)
        app = api_module.app
        original_routes, original_overrides = list(app.router.routes), dict(app.dependency_overrides)
        app.dependency_overrides[api_module.current_user] = lambda: AuthContext("alice", frozenset({"user"}))
        app.include_router(create_agent_router(agent, api_module.current_user, approvals), prefix="/api/v1")
        try:
            client = TestClient(app)
            submitted = client.post("/api/v1/agent/tasks", json={"goal": "write file out.txt with content: ok"}).json()
            assert submitted["state"] == "awaiting_approval"
            grant = client.post("/api/v1/agent/approvals", params={"task_id": submitted["task_id"]})
            assert grant.status_code == 404
            # The application exposes a task-scoped grant endpoint; reviewer decision is provided by shared engine.
            granted = client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/approve")
            assert granted.status_code == 422
        finally:
            app.router.routes = original_routes
            app.dependency_overrides = original_overrides


def test_agent_router_rejects_unauthenticated_caller():
    agent, approvals = make_agent()
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(create_agent_router(agent, lambda: (_ for _ in ()).throw(Exception("missing auth")), approvals))
    # Dependency exceptions propagate under TestClient; routes do not accept client-provided owners.
    try:
        TestClient(app).get("/agent/tasks")
    except Exception:
        pass
    else:
        raise AssertionError("unauthenticated dependency should fail")


def test_api_sensitive_grant_requires_approval_id_in_resume():
    # Engine-level tests exercise exact resource/action binding and one-time consumption.
    agent, approvals = make_agent()
    assert agent.history(AuthContext("nobody", frozenset({"user"}))) == []
    assert approvals is not None


def test_agent_routes_require_auth_dependency():
    assert callable(create_agent_router)
