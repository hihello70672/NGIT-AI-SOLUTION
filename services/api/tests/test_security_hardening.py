"""Adversarial regressions for the security-engine boundaries."""
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


def test_policy_validation_cannot_be_bypassed_with_mutable_roles():
    roles = {"editor"}
    with pytest.raises(ValueError):
        PolicyEngine().register(Policy("file.write", roles))


def test_approval_requires_authorized_different_reviewer_and_exact_scope():
    policies = PolicyEngine()
    policies.register(Policy("agent.approval.decide", frozenset({"admin"})))
    engine = ApprovalEngine(policy_engine=policies)
    pending = engine.request("owner", "file.write", "file-1")
    with pytest.raises(SecurityError):
        engine.decide(pending.approval_id, "reviewer", approved=True, approver_roles={"user"})
    with pytest.raises(SecurityError):
        engine.decide(pending.approval_id, "owner", approved=True, approver_roles={"admin"})
    approved = engine.decide(pending.approval_id, "reviewer", approved=True, approver_roles={"admin"})
    assert approved.status == "approved"
    assert not engine.consume(pending.approval_id, actor_user_id="owner", action="file.write", resource_id="file-2")
    assert engine.consume(pending.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1")
    assert not engine.consume(pending.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1")


def test_restricted_manager_checks_stop_before_consuming_approval():
    audit = AuditLogger()
    policies = PolicyEngine()
    policies.register(Policy("file.write", frozenset({"editor"}), True, True))
    approvals = ApprovalEngine()
    grant = approvals.request("owner", "file.write", "file-1")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policies, approvals, stop, audit)
    context = AuthContext("owner", frozenset({"editor"}))
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(context, "file.write", "file-1", approval_id=grant.approval_id)
    assert approvals.get(grant.approval_id).status == "approved"
    assert audit.events()[-1]["outcome"] == "denied"


def test_concurrent_approval_consumption_has_single_winner():
    engine = ApprovalEngine()
    grant = engine.request("actor", "file.write", "file")
    engine.decide(grant.approval_id, "reviewer", approved=True)
    results = []
    threads = [threading.Thread(target=lambda: results.append(engine.consume(
        grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file"
    ))) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results.count(True) == 1


def test_audit_nested_redaction_and_immutable_snapshots():
    audit = AuditLogger()
    audit.record(action="security.event", details={"nested": [{"api-key": "do-not-log"}], "safe": "ok"})
    snapshot = audit.events()[0]
    assert "do-not-log" not in repr(snapshot)
    with pytest.raises(TypeError):
        snapshot["details"]["safe"] = "changed"
    assert audit.events()[0]["details"]["safe"] == "ok"


def test_auth_roles_are_validated_and_secrets_are_namespaced():
    auth = Authenticator("p" * 32)
    with pytest.raises(ValueError):
        auth.issue("user", {"Admin"})
    assert SecretStore({"VALID_SECRET_2": "example-only"}).get("VALID_SECRET_2") == "example-only"
    with pytest.raises(ValueError):
        SecretStore({}).get("../secret")


def test_expired_approval_and_token_are_denied():
    clock = Clock()
    auth = Authenticator("p" * 32, clock=clock)
    token = auth.issue("actor", {"user"}, ttl_seconds=1)
    clock.now += 1
    with pytest.raises(SecurityError):
        auth.authenticate(token)
    approvals = ApprovalEngine(clock=clock)
    pending = approvals.request("actor", "file.write", "file", ttl_seconds=1)
    approvals.decide(pending.approval_id, "reviewer", approved=True)
    clock.now += 1
    assert not approvals.consume(pending.approval_id, actor_user_id="actor", action="file.write", resource_id="file")
