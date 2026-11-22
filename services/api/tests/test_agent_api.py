"""API tests for authenticated, owner-scoped agent task approvals."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import ApprovalEngine, AuthContext, Policy, PolicyEngine
from services.api.modules.agent.api import create_agent_router
from services.api.modules.agent.runtime import ToolRegistry, build_agent
import tempfile

def test_task_approval_review_and_resume():
    policies = PolicyEngine()
    for name in ("filesystem.write", "browser.navigate", "computer.perform"):
        policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}), True, True))
    policies.register(Policy("agent.approval.decide", frozenset({"admin"})))
    approvals = ApprovalEngine(policy_engine=policies)
    from services.api.security import AuditLogger, EmergencyStop, RestrictedActionManager
    permissions = RestrictedActionManager(policies, approvals, EmergencyStop(AuditLogger()), AuditLogger())
    with tempfile.TemporaryDirectory() as workspace:
        agent = build_agent(ToolRegistry(), permissions, workspace)
        current = lambda: AuthContext("alice", frozenset({"user"}))
        app = FastAPI(); app.include_router(create_agent_router(agent, current, approvals, policies))
        client = TestClient(app)
        task = client.post("/agent/tasks", json={"goal": "write file note.txt with content: hi"}).json()
        assert task["state"] == "awaiting_approval"
        approval = client.post(f"/agent/tasks/{task['task_id']}/approve").json()
        assert approval["status"] == "pending"
        app.dependency_overrides[current] = lambda: AuthContext("admin1", frozenset({"admin"}))
        decision = client.post(f"/agent/approvals/{approval['approval_id']}/decision", json={"approved": True})
        assert decision.status_code == 200
        app.dependency_overrides[current] = lambda: AuthContext("alice", frozenset({"user"}))
        resumed = client.post(f"/agent/tasks/{task['task_id']}/resume", json={"approval_id": approval["approval_id"]})
        assert resumed.status_code == 200 and resumed.json()["state"] == "succeeded"
        assert client.get("/agent/tasks").json()["tasks"]

def test_task_endpoints_enforce_owner():
    policies = PolicyEngine(); approvals = ApprovalEngine(policy_engine=policies)
    from services.api.security import AuditLogger, EmergencyStop, RestrictedActionManager
    audit = AuditLogger(); agent = build_agent(ToolRegistry(), RestrictedActionManager(policies, approvals, EmergencyStop(audit), audit), tempfile.gettempdir())
    alice = AuthContext("alice", frozenset({"user"})); bob = AuthContext("bob", frozenset({"user"}))
    app = FastAPI(); app.include_router(create_agent_router(agent, lambda: alice))
    client = TestClient(app); task = client.post("/agent/tasks", json={"goal": "read file missing.txt"}).json()
    assert task["state"] == "failed"
    app.dependency_overrides[lambda: alice] = lambda: bob
    assert client.get(f"/agent/tasks/{task['task_id']}").status_code == 404

if __name__ == "__main__":
    test_task_approval_review_and_resume()
    test_task_endpoints_enforce_owner()
