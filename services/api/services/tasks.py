"""Small background-task contract for accepted/rejected work submissions.

This deliberately defines an in-process interface only; durable execution and
cross-process task state require a separately approved runner and persistence.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Callable, Any
from uuid import uuid4

@dataclass(frozen=True)
class TaskStatus:
    task_id: str
    state: str
    submitted_at: str
    result: Any = None
    error: str | None = None

class TaskRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._tasks: dict[str, TaskStatus] = {}

    def submit(self, operation: Callable[[], Any]) -> TaskStatus:
        if not callable(operation):
            raise TypeError("task operation must be callable")
        task_id = str(uuid4())
        submitted = datetime.now(timezone.utc).isoformat()
        accepted = TaskStatus(task_id, "accepted", submitted)
        with self._lock:
            self._tasks[task_id] = accepted
        try:
            result = operation()
        except Exception:
            failed = TaskStatus(task_id, "failed", submitted, error="Task execution failed")
            with self._lock:
                self._tasks[task_id] = failed
            return failed
        complete = TaskStatus(task_id, "succeeded", submitted, result=result)
        with self._lock:
            self._tasks[task_id] = complete
        return accepted

    def get(self, task_id: str) -> TaskStatus | None:
        with self._lock:
            return self._tasks.get(task_id)
