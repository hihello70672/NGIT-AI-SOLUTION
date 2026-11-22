"""In-process task submission contract; intentionally not a durable queue.

Tasks expose an accepted identifier and terminal outcome. Owner/correlation metadata is
validated and retained for local polling. Persistence, retries, cancellation, and
cross-worker delivery require a separately approved durable runner.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

@dataclass(frozen=True)
class TaskStatus:
    task_id: str
    state: str
    submitted_at: str
    owner_id: str | None = None
    correlation_id: str | None = None
    result: Any = None
    error: str | None = None

class TaskRegistry:
    def __init__(self) -> None:
        self._lock=RLock();self._tasks:dict[str,TaskStatus]={}

    def submit(self, operation:Callable[[],Any], *, owner_id:str|None=None, correlation_id:str|None=None) -> TaskStatus:
        if not callable(operation):raise TypeError("task operation must be callable")
        for value in (owner_id,correlation_id):
            if value is not None and (not isinstance(value,str) or not value or len(value)>256):raise ValueError("invalid task context")
        task_id=str(uuid4());submitted=datetime.now(timezone.utc).isoformat()
        accepted=TaskStatus(task_id,"accepted",submitted,owner_id,correlation_id)
        with self._lock:self._tasks[task_id]=accepted
        try:
            result=operation()
        except Exception:
            failed=TaskStatus(task_id,"failed",submitted,owner_id,correlation_id,error="Task execution failed")
            with self._lock:self._tasks[task_id]=failed
        else:
            complete=TaskStatus(task_id,"succeeded",submitted,owner_id,correlation_id,result=result)
            with self._lock:self._tasks[task_id]=complete
        return accepted

    def get(self, task_id:str, *, owner_id:str|None=None)->TaskStatus|None:
        with self._lock:
            task=self._tasks.get(task_id)
            if task is None or task.owner_id != owner_id:return None
            return task
