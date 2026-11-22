from services.api.services.tasks import TaskRegistry

def test_task_registry_reports_submission_and_completion():
    registry = TaskRegistry()
    submitted = registry.submit(lambda: "done")
    assert submitted.state == "accepted"
    assert registry.get(submitted.task_id).state == "succeeded"

def test_task_registry_reports_safe_failure():
    registry = TaskRegistry()
    result = registry.submit(lambda: (_ for _ in ()).throw(RuntimeError("private detail")))
    assert result.state == "failed"
    assert result.error == "Task execution failed"
    assert "private detail" not in repr(result)
