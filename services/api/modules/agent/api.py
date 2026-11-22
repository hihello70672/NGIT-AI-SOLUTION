"""Authenticated REST endpoints for Personal Agent tasks and approvals."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.api.security import AuthContext, SecurityError
from services.api.modules.agent.runtime import AgentError, AgentService, public_record


def create_agent_router(agent: AgentService, current_user: Any, approvals: Any = None, policies: Any = None) -> APIRouter:
    router = APIRouter(prefix="/agent", tags=["agent"])

    class TaskInput(BaseModel):
        goal: str = Field(min_length=1, max_length=4000)

    class ApprovalInput(BaseModel):
        approval_id: str = Field(min_length=1, max_length=128)

    class DecisionInput(BaseModel):
        approved: bool

    def invoke(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AgentError as exc:
            status = 404 if exc.code == "task_not_found" else 409 if exc.code in {"task_running", "invalid_task_state"} else 422
            raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message}) from exc
        except SecurityError as exc:
            raise HTTPException(status_code=401 if exc.code == "unauthenticated" else 403,
                                detail={"code": exc.code, "message": exc.message}) from exc

    @router.get("/tools")
    def list_tools(context: AuthContext = Depends(current_user)):
        return {"tools": agent.tools.list()}

    @router.post("/tasks", status_code=202)
    def submit(body: TaskInput, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.submit, context, body.goal))

    @router.get("/tasks")
    def history(limit: int = Query(50, ge=1, le=100), context: AuthContext = Depends(current_user)):
        return {"tasks": [public_record(row) for row in invoke(agent.history, context, limit)]}

    @router.get("/tasks/{task_id}")
    def get_task(task_id: str, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.get, context, task_id))

    @router.post("/tasks/{task_id}/approve")
    def request_approval(task_id: str, context: AuthContext = Depends(current_user)):
        if approvals is None:
            raise HTTPException(status_code=503, detail={"code": "approval_unavailable", "message": "Approval workflow unavailable"})
        record = invoke(agent.get, context, task_id)
        pending = next((item for item in record.observations if item.get("state") == "approval_required"), None)
        if record.state != "awaiting_approval" or pending is None:
            raise HTTPException(status_code=409, detail={"code": "approval_not_required", "message": "Task has no pending approval"})
        if record.pending_approval_id:
            return {"task_id": task_id, "approval_id": record.pending_approval_id, "action": pending["action"], "resource_id": pending["resource_id"], "status": "pending"}
        try:
            grant = approvals.request(context.user_id, pending["action"], pending["resource_id"])
        except SecurityError as exc:
            raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message}) from exc
        record.pending_approval_id = grant.approval_id
        return {"task_id": task_id, "approval_id": grant.approval_id, "action": pending["action"], "resource_id": pending["resource_id"], "status": grant.status}

    @router.post("/approvals/{approval_id}/decision")
    def decide(approval_id: str, body: DecisionInput, context: AuthContext = Depends(current_user)):
        if approvals is None:
            raise HTTPException(status_code=503, detail={"code": "approval_unavailable", "message": "Approval workflow unavailable"})
        grant = approvals.get(approval_id)
        if grant is None:
            raise HTTPException(status_code=404, detail={"code": "approval_not_found", "message": "Approval not found"})
        if context.user_id == grant.actor_user_id:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "A different reviewer is required"})
        if policies is None:
            raise HTTPException(status_code=503, detail={"code": "policy_unavailable", "message": "Reviewer authorization unavailable"})
        try:
            policies.authorize(context, "agent.approval.decide")
            result = approvals.decide(approval_id, context.user_id, approved=body.approved, approver_roles=context.roles)
        except SecurityError as exc:
            raise HTTPException(status_code=403 if exc.code != "approval_invalid" else 409,
                                detail={"code": exc.code, "message": exc.message}) from exc
        return {"approval_id": result.approval_id, "status": result.status}

    @router.post("/tasks/{task_id}/resume")
    def resume(task_id: str, body: ApprovalInput, context: AuthContext = Depends(current_user)):
        record = invoke(agent.get, context, task_id)
        if record.pending_approval_id != body.approval_id:
            raise HTTPException(status_code=403, detail={"code": "approval_scope_mismatch", "message": "Approval does not belong to this task"})
        return public_record(invoke(agent.execute, context, task_id, body.approval_id))

    @router.post("/tasks/{task_id}/reject")
    def reject(task_id: str, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.reject, context, task_id))

    return router


create_router = create_agent_router
__all__ = ["create_agent_router", "create_router"]
