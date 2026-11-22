import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService, AgentPlan, PlannedStep
from services.api.security import AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, PolicyEngine, RestrictedActionManager, Policy

class StaticPlanner:
    def plan(self, owner, goal): return AgentPlan("api-task", owner, goal, (PlannedStep("safe.echo", {"value": goal}, "echo"),), "now")

def test_authenticated_owner_scoped_routes():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    tools = ToolRegistry(); tools.register(ToolDefinition("safe.echo", "safe echo", False, lambda a: ToolResult(a["value"], "echoed", True)))
    agent = AgentService(tools, permissions, StaticPlanner()); app = FastAPI()
    app.include_router(create_agent_router(agent, lambda: AuthContext("alice", frozenset({"user"})), approvals), prefix="/api/v1")
    client = TestClient(app)
    submitted = client.post("/api/v1/agent/tasks", json={"goal": "hello"})
    assert submitted.status_code == 202 and submitted.json()["state"] == "succeeded"
    assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"] == "hello"

def test_sensitive_approval_routes_require_reviewer_and_exact_resume():
    import tempfile
    from services.api.modules.agent.runtime import build_agent
    audit = AuditLogger(); policies = PolicyEngine()
    policies.register(Policy("agent.tool.filesystem.write", frozenset({"user"}), True, True))
    approvals = ApprovalEngine(); permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    with tempfile.TemporaryDirectory() as workspace:
        agent = build_agent(ToolRegistry(), permissions, workspace); app = FastAPI()
        owner = AuthContext("alice", frozenset({"user"})); reviewer = AuthContext("reviewer", frozenset({"user"}))
        app.include_router(create_agent_router(agent, lambda: owner, approvals), prefix="/api/v1")
        client = TestClient(app); task = client.post("/api/v1/agent/tasks", json={"goal": "write file out.txt with content: ok"}).json()
        assert task["state"] == "awaiting_approval"
        grant = client.post(f"/api/v1/agent/tasks/{task['task_id']}/approve").json()
        assert client.post(f"/api/v1/agent/approvals/{grant['approval_id']}/decision", json={"approved": True}).status_code == 403
        app.dependency_overrides[next(d.call for r in app.routes if getattr(r, "path", "").endswith("/decision") for d in r.dependant.dependencies)] = lambda: reviewer
        decision = client.post(f"/api/v1/agent/approvals/{grant['approval_id']}/decision", json={"approved": True})
        assert decision.status_code == 200 and decision.json()["status"] == "approved"
        resumed = client.post(f"/api/v1/agent/tasks/{task['task_id']}/resume", json={"approval_id": grant["approval_id"]})
        assert resumed.status_code == 200 and resumed.json()["state"] == "succeeded"
        assert open(os.path.join(workspace, "out.txt"), encoding="utf-8").read() == "ok"
