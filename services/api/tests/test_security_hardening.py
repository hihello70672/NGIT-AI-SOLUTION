"""Adversarial regression tests for the security-engine boundaries."""
import threading

import pytest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecretStore, SecurityError,
)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def test_policy_deny_by_default_and_reject_malformed_and_duplicate_rules():
    engine = PolicyEngine()
    engine.register(Policy("file.write", frozenset({"editor"})))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("a", frozenset({"editor"})), "unregistered.action")
    with pytest.raises(ValueError):
        engine.register(Policy("restricted.action", frozenset({"user"}), restricted=True))
    with pytest.raises(ValueError):
        engine.register(Policy("file.write", frozenset({"editor"})))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("a", frozenset({"editor"})), "file.write", owner_id="b")


def test_approval_requires_separate_authorized_reviewer_and_exact_scope():
    policies = PolicyEngine()
    policies.register(Policy("agent.approval.decide", frozenset({"admin"})))
    approvals = ApprovalEngine(policy_engine=policies)
    request = approvals.request("owner", "file.write", "file-1")
    with pytest.raises(SecurityError):
        approvals.decide(request.approval_id, "owner", approved=True, approver_roles={"admin"})
    with pytest.raises(SecurityError):
        approvals.decide(request.approval_id, "reviewer", approved=True, approver_roles={"user"})
    approvals.decide(request.approval_id, "reviewer", approved=True, approver_roles={"admin"})
    assert not approvals.consume(request.approval_id, actor_user_id="owner", action="file.write", resource_id="file-2")
    outcomes = []
    workers = [threading.Thread(target=lambda: outcomes.append(approvals.consume(
        request.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1"))) for _ in range(12)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert outcomes.count(True) == 1


def test_restricted_action_checks_stop_before_consuming_approval_and_audits_denials():
    audit = AuditLogger()
    policies = PolicyEngine()
    policies.register(Policy("file.write", frozenset({"editor"}), approval_required=True, restricted=True))
    approvals = ApprovalEngine()
    request = approvals.request("owner", "file.write", "file-1")
    approvals.decide(request.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policies, approvals, stop, audit)
    caller = AuthContext("owner", frozenset({"editor"}))
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(caller, "file.write", "file-1", approval_id=request.approval_id)
    assert approvals.get(request.approval_id).status == "approved"
    stop.reset("admin")
    manager.authorize(caller, "file.write", "file-1", approval_id=request.approval_id)
    assert approvals.get(request.approval_id).status == "consumed"
    with pytest.raises(SecurityError):
        manager.authorize(caller, "file.write", "file-1", approval_id=request.approval_id)
    assert [item["outcome"] for item in audit.events() if item["action"] == "file.write"] == ["denied", "authorized", "denied"]


def test_approval_expiry_and_token_parameter_validation():
    clock = Clock()
    approvals = ApprovalEngine(clock=clock)
    pending = approvals.request("owner", "file.write", "file", ttl_seconds=1)
    approvals.decide(pending.approval_id, "reviewer", approved=True)
    clock.now += 1
    assert not approvals.consume(pending.approval_id, actor_user_id="owner", action="file.write", resource_id="file")
    auth = Authenticator("p" * 32, clock=clock)
    with pytest.raises(ValueError):
        auth.issue("user", ttl_seconds=True)
    token = auth.issue("user", {"user"})
    auth.revoke(token)
    with pytest.raises(SecurityError):
        auth.authenticate(token)


def test_audit_recursively_redacts_secrets_and_snapshots_are_immutable():
    audit = AuditLogger()
    audit.record(action="example", details={"nested": [{"api-key": "never-log-me"}], "safe": "value"})
    snapshot = audit.events()[0]
    assert "never-log-me" not in repr(snapshot)
    with pytest.raises(TypeError):
        snapshot["details"]["safe"] = "tampered"
    assert audit.events()[0]["details"]["safe"] == "value"
    with pytest.raises(TypeError):
        snapshot["details"]["nested"][0]["api-key"] = "tampered"
    assert len(SecretStore({"VALID_SECRET_2": "example-only"}).get("VALID_SECRET_2")) > 0
    with pytest.raises(ValueError):
        SecretStore({}).get("../secret")


def test_approval_decisions_cannot_be_replayed_or_consumed_twice():
    engine = ApprovalEngine()
    approval = engine.request("actor", "file.write", "file")
    engine.decide(approval.approval_id, "reviewer", approved=False)
    with pytest.raises(SecurityError):
        engine.decide(approval.approval_id, "reviewer-2", approved=True)
    assert not engine.consume(approval.approval_id, actor_user_id="actor", action="file.write", resource_id="file")
