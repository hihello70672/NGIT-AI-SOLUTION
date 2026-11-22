"""Authenticated REST endpoints for Personal Agent tasks and approval requests."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from services.api.security import AuthContext, SecurityError
from services.api.modules.agent.runtime import AgentError, AgentService, public_record


def create_router(agent: AgentService, current_user: Any, approvals: Any | None = None) -> APIRouter:
    router = APIRouter(prefix="/agent", tags=["agent"])

    class TaskInput(BaseModel):
        goal: str = Field(min_length=1, max_length=4000)

    class ApprovalInput(BaseModel):
        approval_id: str = Field(min_length=1, max_length=128)

    def invoke(fn, *args):
        try:
            return fn(*args)
        except AgentError as exc:
            status = 404 if exc.code == "task_not_found" else 422
            raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message}) from exc
        except SecurityError as exc:
            raise HTTPException(status_code=401 if exc.code == "unauthenticated" else 403,
                                detail={"code": exc.code, "message": exc.message}) from exc

    @router.get("/tools")
    def list_tools(context: AuthContext = Depends(current_user)):
        del context
        return {"tools": agent.tools.list()}

    @router.post("/tasks", status_code=202)
    def submit(body: TaskInput, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.submit, context, body.goal))

    @router.get("/tasks")
    def history(limit: int = Query(default=50, ge=1, le=100), context: AuthContext = Depends(current_user)):
        return {"tasks": [public_record(item) for item in invoke(agent.history, context, limit)]}

    @router.get("/tasks/{task_id}")
    def get_task(task_id: str, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.get, context, task_id))

    @router.post("/tasks/{task_id}/approve")
    def approve(task_id: str, body: ApprovalInput, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.approve_and_resume, context, task_id, body.approval_id))

    @router.post("/tasks/{task_id}/reject")
    def reject(task_id: str, context: AuthContext = Depends(current_user)):
        return public_record(invoke(agent.reject, context, task_id))

    @router.post("/approvals", status_code=201)
    def request_approval(task_id: str = Query(min_length=1, max_length=128),
                         context: AuthContext = Depends(current_user)):
        if approvals is None:
            raise HTTPException(status_code=503, detail={"code": "approval_unavailable", "message": "Approval request service is unavailable"})
        record = invoke(agent.get, context, task_id)
        pending = next((item for item in record.observations if item.get("state") == "approval_required"), None)
        if record.state != "awaiting_approval" or pending is None:
            raise HTTPException(status_code=409, detail={"code": "approval_not_required", "message": "Task has no pending approval"})
        approval = approvals.request(context.user_id, pending["action"], pending["resource_id"])
        record.pending_approval_id = approval.approval_id
        return {"task_id": task_id, "approval_id": approval.approval_id, "action": pending["action"],
                "resource_id": pending["resource_id"], "status": approval.status}

    return router
