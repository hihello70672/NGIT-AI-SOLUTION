import os
os.environ.setdefault("AUTH_TOKEN_PEPPER","test-auth-pepper-value-at-least-32-bytes")
os.environ.setdefault("PASSWORD_PEPPER","test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as api_module
from services.api.modules.agent.api import create_router
from services.api.modules.agent.runtime import ToolRegistry, ToolDefinition, ToolResult, AgentService
from services.api.security import AuthContext, ApprovalEngine, AuditLogger, EmergencyStop, PolicyEngine, RestrictedActionManager

class StaticPlanner:
    def plan(self, owner, goal):
        from services.api.modules.agent.runtime import AgentPlan, PlannedStep
        return AgentPlan("task-one", owner, goal, (PlannedStep("safe.echo", {"value":goal}, "Echo goal"),), "now")

def test_authenticated_agent_api_owner_scoped_tasks(monkeypatch):
    audit=AuditLogger(); policies=PolicyEngine(); approvals=ApprovalEngine(); permissions=RestrictedActionManager(policies,approvals,EmergencyStop(audit),audit)
    tools=ToolRegistry(); tools.register(ToolDefinition("safe.echo","safe echo",False,lambda args:ToolResult(args["value"],"echoed",True)))
    agent=AgentService(tools,permissions,StaticPlanner())
    app=api_module.app; original=list(app.router.routes)
    app.include_router(create_router(agent,lambda:AuthContext("alice",frozenset({"user"})),approvals),prefix="/api/v1")
    try:
        client=TestClient(app)
        assert client.post("/api/v1/agent/tasks",json={"goal":"hello"}).json()["state"]=="succeeded"
        assert client.get("/api/v1/agent/tasks").json()["tasks"][0]["result"]=="hello"
    finally: app.router.routes=original
