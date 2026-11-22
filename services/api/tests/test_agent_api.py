"""API tests for agent approval separation and reviewer RBAC."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import ApprovalEngine, AuthContext, Policy, PolicyEngine
from services.api.modules.agent.api import create_agent_router

class Record:
    def __init__(self, approval_id=None):
        self.state="awaiting_approval"; self.observations=[{"state":"approval_required","action":"file.write","resource_id":"file-1"}]
        self.pending_approval_id=approval_id; self.owner_user_id="owner"
class Agent:
    def __init__(self): self.record=Record()
    def get(self,context,task_id):
        if context.user_id!=self.record.owner_user_id: raise ValueError("not owner")
        return self.record
class Tools:
    def list(self): return []

def client_for(context, approvals, policies):
    app=FastAPI(); app.include_router(create_agent_router(Agent(),lambda:context,approvals,policies))
    return TestClient(app)

def test_approval_decision_requires_admin_and_different_reviewer():
    approvals=ApprovalEngine(); grant=approvals.request("owner","file.write","file-1")
    policies=PolicyEngine(); policies.register(Policy("agent.approval.decide",frozenset({"admin"})))
    owner=client_for(AuthContext("owner",frozenset({"user"})),approvals,policies)
    assert owner.post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
    outsider=client_for(AuthContext("reviewer",frozenset({"user"})),approvals,policies)
    assert outsider.post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
    reviewer=client_for(AuthContext("reviewer",frozenset({"admin"})),approvals,policies)
    response=reviewer.post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True})
    assert response.status_code==200 and response.json()["status"]=="approved"

def test_approval_engine_reviewer_separation_is_enforced_even_without_api():
    approvals=ApprovalEngine(); grant=approvals.request("owner","file.write","file-1")
    try:
        approvals.decide(grant.approval_id,"owner",approved=True)
    except Exception as exc:
        assert getattr(exc,"code",None)=="forbidden"
    else:
        raise AssertionError("task owner must not approve own request")

def test_authentication_and_authorization_rejections_use_http_boundary():
    approvals=ApprovalEngine(); grant=approvals.request("owner","file.write","file-1")
    policies=PolicyEngine(); policies.register(Policy("agent.approval.decide",frozenset({"admin"})))
    client=client_for(AuthContext("owner",frozenset({"user"})),approvals,policies)
    assert client.post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
