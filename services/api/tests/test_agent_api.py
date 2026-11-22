import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService, AgentPlan, PlannedStep
from services.api.security import (AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, PolicyEngine,
    RestrictedActionManager, Policy)

class StaticPlanner:
    def plan(self, owner, goal): return AgentPlan("api-task", owner, goal, (PlannedStep("safe.echo", {"value": goal}, "echo"),), "now")

def setup_app():
    audit = AuditLogger(); policies = PolicyEngine()
    policies.register(Policy("agent.tool.filesystem.write", frozenset({"user"}), True, True))
    approvals = ApprovalEngine(); perms = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    tools = ToolRegistry(); tools.register(ToolDefinition("safe.echo", "safe echo", False, lambda a: ToolResult(a["value"], "echoed", True)))
    service = AgentService(tools, perms, StaticPlanner()); app = FastAPI()
    app.include_router(create_agent_router(service, lambda: AuthContext("alice", frozenset({"user"})), approvals), prefix="/api/v1")
    return app

def test_authenticated_owner_scoped_routes():
    client = TestClient(setup_app())
    submitted = client.post("/api/v1/agent/tasks", json={"goal": "hello"})
    assert submitted.status_code == 202 and submitted.json()["state"] == "succeeded"
    assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"] == "hello"

def test_sensitive_approval_routes_require_reviewer_and_resume():
    # The task owner can ask for a grant but cannot make the approval decision.
    audit = AuditLogger(); policies = PolicyEngine()
    policies.register(Policy("agent.tool.filesystem.write", frozenset({"user"}), True, True))
    approvals = ApprovalEngine(); perms = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    import tempfile
    from services.api.modules.agent.runtime import build_agent
    with tempfile.TemporaryDirectory() as workspace:
        agent = build_agent(ToolRegistry(), perms, workspace)
        app = FastAPI()
        app.include_router(create_agent_router(agent, lambda: AuthContext("alice", frozenset({"user"})), approvals), prefix="/api/v1")
        client = TestClient(app)
        record = client.post("/api/v1/agent/tasks", json={"goal": "write file out.txt with content: ok"}).json()
        assert record["state"] == "awaiting_approval"
        grant = client.post(f"/api/v1/agent/tasks/{record['task_id']}/approve").json()
        assert client.post(f"/api/v1/agent/approvals/{grant['approval_id']}/decision", json={"approved": True}).status_code == 403
        app.dependency_overrides[next(d.call for r in app.routes if getattr(r, "path", "").endswith("/decision") for d in r.dependant.dependencies)] = lambda: AuthContext("reviewer", frozenset({"user"}))
        assert client.post(f"/api/v1/agent/approvals/{grant['approval_id']}/decision", json={"approved": True}).json()["status"] == "approved"
        assert client.post(f"/api/v1/agent/tasks/{record['task_id']}/resume", json={"approval_id": grant["approval_id"]}).json()["state"] == "succeeded"
