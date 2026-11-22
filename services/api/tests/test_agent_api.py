import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as api_module
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService
from services.api.security import AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, PolicyEngine, RestrictedActionManager, Policy


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


def mount_agent(agent, approvals):
    app = api_module.app
    original_routes, original_overrides = list(app.router.routes), dict(app.dependency_overrides)
    app.dependency_overrides[api_module.current_user] = lambda: AuthContext("alice", frozenset({"user"}))
    app.include_router(create_agent_router(agent, api_module.current_user, approvals), prefix="/api/v1")
    return app, original_routes, original_overrides


def restore_agent(app, routes, overrides):
    app.router.routes = routes
    app.dependency_overrides = overrides


def test_authenticated_agent_routes_are_owner_scoped():
    agent, approvals = make_agent()
    app, routes, overrides = mount_agent(agent, approvals)
    try:
        client = TestClient(app)
        submitted = client.post("/api/v1/agent/tasks", json={"goal": "hello"})
        assert submitted.status_code == 202 and submitted.json()["state"] == "succeeded"
        assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"] == "hello"
    finally:
        restore_agent(app, routes, overrides)


def test_sensitive_approval_requires_distinct_reviewer_and_exact_resume():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    policies.register(Policy("agent.tool.filesystem.write", frozenset({"user"}), True, True))
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    import tempfile
    from services.api.modules.agent.runtime import build_agent
    with tempfile.TemporaryDirectory() as workspace:
        agent = build_agent(ToolRegistry(), permissions, workspace)
        app, routes, overrides = mount_agent(agent, approvals)
        try:
            client = TestClient(app)
            submitted = client.post("/api/v1/agent/tasks", json={"goal": "write file out.txt with content: ok"}).json()
            assert submitted["state"] == "awaiting_approval"
            grant_response = client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/approve")
            assert grant_response.status_code == 200
            grant = grant_response.json()
            self_decision = client.post(f"/api/v1/agent/approvals/{grant['approval_id']}/decision", json={"approved": True})
            assert self_decision.status_code == 403
            approvals.decide(grant["approval_id"], "reviewer", approved=True)
            resumed = client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/resume", json={"approval_id": grant["approval_id"]})
            assert resumed.status_code == 200 and resumed.json()["state"] == "succeeded"
            assert client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/resume", json={"approval_id": grant["approval_id"]}).status_code == 200
        finally:
            restore_agent(app, routes, overrides)


def test_owner_cannot_read_another_tasks():
    agent, _ = make_agent()
    first = agent.submit(AuthContext("alice", frozenset({"user"})), "alice task")
    from services.api.modules.agent.runtime import AgentError
    try:
        agent.get(AuthContext("bob", frozenset({"user"})), first.task_id)
    except AgentError as exc:
        assert exc.code == "task_not_found"
    else:
        raise AssertionError("cross-owner access must fail closed")


def test_sensitive_grant_engine_enforces_separation_of_duties():
    engine = ApprovalEngine()
    grant = engine.request("alice", "agent.tool.filesystem.write", "task:0")
    from services.api.security import SecurityError
    try:
        engine.decide(grant.approval_id, "alice", approved=True)
    except SecurityError as exc:
        assert exc.code == "forbidden"
    else:
        raise AssertionError("requester cannot approve their own action")


def test_router_is_created_with_authentication_dependency():
    agent, approvals = make_agent()
    from fastapi import FastAPI
    app = FastAPI()
    router = create_agent_router(agent, lambda: AuthContext("alice", frozenset({"user"})), approvals)
    app.include_router(router)
    assert any(route.path == "/agent/tasks" for route in app.routes)
