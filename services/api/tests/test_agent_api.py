"""API tests for agent approval separation and reviewer RBAC."""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from services.api.security import ApprovalEngine, AuthContext, Policy, PolicyEngine
from services.api.modules.agent.api import create_agent_router

class Record:
    def __init__(self):
        self.state="awaiting_approval";self.observations=[{"state":"approval_required","action":"file.write","resource_id":"file-1"}]
        self.pending_approval_id=None;self.owner_user_id="owner"
class Agent:
    def __init__(self):self.record=Record()
    def get(self,context,task_id):
        if context.user_id!=self.record.owner_user_id:raise HTTPException(status_code=404,detail={"code":"task_not_found","message":"Task was not found"})
        return self.record
def client_for(context,approvals,policies):
    app=FastAPI();app.include_router(create_agent_router(Agent(),lambda:context,approvals,policies));return TestClient(app)
def test_approval_decision_requires_admin_and_different_reviewer():
    policies=PolicyEngine();policies.register(Policy("agent.approval.decide",frozenset({"admin"})));approvals=ApprovalEngine(policy_engine=policies)
    grant=approvals.request("owner","file.write","file-1")
    assert client_for(AuthContext("owner",frozenset({"user"})),approvals,policies).post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
    assert client_for(AuthContext("reviewer",frozenset({"user"})),approvals,policies).post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
    response=client_for(AuthContext("reviewer",frozenset({"admin"})),approvals,policies).post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True})
    assert response.status_code==200 and response.json()["status"]=="approved"
def test_missing_policy_engine_fails_closed_for_reviewer_route():
    approvals=ApprovalEngine();grant=approvals.request("owner","file.write","file-1")
    response=client_for(AuthContext("reviewer",frozenset({"admin"})),approvals,None).post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True})
    assert response.status_code==503 and approvals.get(grant.approval_id).status=="pending"
def test_non_owner_cannot_access_task_approval_endpoint():
    policies=PolicyEngine();policies.register(Policy("agent.approval.decide",frozenset({"admin"})));approvals=ApprovalEngine(policy_engine=policies)
    client=client_for(AuthContext("reviewer",frozenset({"admin"})),approvals,policies)
    assert client.post("/agent/tasks/private-task/approve").status_code==404

def test_task_owner_cannot_decide_even_with_admin_role():
    policies=PolicyEngine();policies.register(Policy("agent.approval.decide",frozenset({"admin"})));approvals=ApprovalEngine(policy_engine=policies)
    grant=approvals.request("owner","file.write","file-1")
    client=client_for(AuthContext("owner",frozenset({"admin"})),approvals,policies)
    assert client.post(f"/agent/approvals/{grant.approval_id}/decision",json={"approved":True}).status_code==403
