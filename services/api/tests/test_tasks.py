from services.api.services.tasks import TaskRegistry

def test_task_submission_result_and_owner_scope():
    registry=TaskRegistry();accepted=registry.submit(lambda:"done",owner_id="u1",correlation_id="req1")
    assert accepted.state=="accepted"
    final=registry.get(accepted.task_id,owner_id="u1")
    assert final.state=="succeeded" and final.result=="done" and final.correlation_id=="req1"
    assert registry.get(accepted.task_id,owner_id="u2") is None

def test_failure_redacts_exception_and_invalid_context():
    registry=TaskRegistry()
    failed=registry.submit(lambda:(_ for _ in ()).throw(RuntimeError("secret detail")))
    assert registry.get(failed.task_id).state=="failed"
    assert registry.get(failed.task_id).error=="Task execution failed"
    assert "secret detail" not in repr(registry.get(failed.task_id))
    try:registry.submit(lambda:None,owner_id="")
    except ValueError:pass
    else:raise AssertionError("empty task owner accepted")
