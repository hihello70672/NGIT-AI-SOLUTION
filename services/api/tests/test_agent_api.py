import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER", "test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as api_module
from services.api.modules.agent.api import create_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService
from services.api.security import AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, Policy, PolicyEngine, RestrictedActionManager

class StaticPlanner:
    def plan(self, owner, goal):
        from services.api.modules.agent.runtime import AgentPlan, PlannedStep
        return AgentPlan("task-one", owner, goal, (PlannedStep("safe.echo", {"value": goal}, "Echo goal"),), "now")

def test_authenticated_agent_api_owner_scoped_tasks():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    tools = ToolRegistry()
    tools.register(ToolDefinition("safe.echo", "safe echo", False, lambda args: ToolResult(args["value"], "echoed", True)))
    agent = AgentService(tools, permissions, StaticPlanner())
    app = api_module.app; original_routes = list(app.router.routes); original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[api_module.current_user] = lambda: AuthContext("alice", frozenset({"user"}))
    app.include_router(create_router(agent, api_module.current_user, approvals), prefix="/api/v1")
    try:
        client = TestClient(app)
        submitted = client.post("/api/v1/agent/tasks", json={"goal": "hello"})
        assert submitted.status_code == 202 and submitted.json()["state"] == "succeeded"
        assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"] == "hello"
    finally:
        app.router.routes = original_routes; app.dependency_overrides = original_overrides

def test_shared_approval_workflow_required_before_sensitive_action():
    audit = AuditLogger(); policies = PolicyEngine(); approvals = ApprovalEngine()
    action = "agent.tool.filesystem.write"
    policies.register(Policy(action, frozenset({"user"}), approval_required=True, restricted=True))
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit)
    from services.api.modules.agent.runtime import build_agent
    import tempfile
    with tempfile.TemporaryDirectory() as workspace:
        tools = ToolRegistry(); agent = build_agent(tools, permissions, workspace)
        original = list(api_module.app.router.routes); overrides = dict(api_module.app.dependency_overrides)
        api_module.app.dependency_overrides[api_module.current_user] = lambda: AuthContext("alice", frozenset({"user"}))
        api_module.app.include_router(create_router(agent, api_module.current_user, approvals), prefix="/api/v1")
        try:
            client = TestClient(api_module.app)
            submitted = client.post("/api/v1/agent/tasks", json={"goal": "write file out.txt with content: ok"}).json()
            assert submitted["state"] == "awaiting_approval"
            requested = client.post("/api/v1/agent/approvals", params={"task_id": submitted["task_id"]})
            assert requested.status_code == 201
            grant = requested.json()
            approvals.decide(grant["approval_id"], "reviewer", approved=True)
            resumed = client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/approve", json={"approval_id": grant["approval_id"]})
            assert resumed.status_code == 200 and resumed.json()["state"] == "succeeded"
            assert client.post(f"/api/v1/agent/tasks/{submitted['task_id']}/approve", json={"approval_id": grant["approval_id"]}).status_code == 409
        finally:
            api_module.app.router.routes = original; api_module.app.dependency_overrides = overrides
