"""Adversarial regression tests for authentication and authorization boundaries."""
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


def test_policy_values_are_immutable_and_admin_is_not_an_owner_bypass_by_default():
    roles = frozenset({"editor"})
    policy = Policy("file.write", roles)
    engine = PolicyEngine()
    engine.register(policy)
    assert engine.authorize(AuthContext("a", roles), "file.write", owner_id="a") is policy
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("admin", frozenset({"admin"})), "file.write", owner_id="a")
    with pytest.raises(ValueError):
        PolicyEngine().register(Policy("file.write", {"editor"}))


def test_approval_requires_separate_admin_reviewer_and_exact_one_time_scope():
    policies = PolicyEngine()
    policies.register(Policy("admin.approvals.decide", frozenset({"admin"})))
    engine = ApprovalEngine(policy_engine=policies)
    approval = engine.request("owner", "file.write", "file-1")
    with pytest.raises(SecurityError):
        engine.decide(approval.approval_id, "reviewer", approved=True, approver_roles={"user"})
    with pytest.raises(SecurityError):
        engine.decide(approval.approval_id, "owner", approved=True, approver_roles={"admin"})
    engine.decide(approval.approval_id, "reviewer", approved=True, approver_roles={"admin"})
    assert not engine.consume(approval.approval_id, actor_user_id="owner", action="file.write", resource_id="other")
    assert engine.consume(approval.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1")
    assert not engine.consume(approval.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1")


def test_approval_expiry_and_atomic_single_consumer():
    clock, engine = Clock(), ApprovalEngine(clock=Clock())
    grant = engine.request("actor", "file.write", "file", ttl_seconds=1)
    engine.decide(grant.approval_id, "reviewer", approved=True)
    outcomes = []
    threads = [threading.Thread(target=lambda: outcomes.append(engine.consume(
        grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file"))) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count(True) == 1
    expired = ApprovalEngine(clock=clock)
    item = expired.request("actor", "file.write", "file", ttl_seconds=1)
    expired.decide(item.approval_id, "reviewer", approved=True)
    clock.now += 1
    assert not expired.consume(item.approval_id, actor_user_id="actor", action="file.write", resource_id="file")


def test_restricted_manager_audits_denial_without_burning_approval_during_stop():
    audit = AuditLogger()
    policies = PolicyEngine()
    policies.register(Policy("file.write", frozenset({"editor"}), True, True))
    approvals = ApprovalEngine()
    grant = approvals.request("owner", "file.write", "file")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policies, approvals, stop, audit)
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(AuthContext("owner", frozenset({"editor"})), "file.write", "file", approval_id=grant.approval_id)
    assert approvals.get(grant.approval_id).status == "approved"
    assert audit.events()[-1]["outcome"] == "denied"


def test_audit_redacts_nested_secret_fields_and_is_immutable():
    audit = AuditLogger()
    audit.record(action="test", details={"nested": [{"api_key": "never-log", "safe": "ok"}]})
    snapshot = audit.events()[0]
    assert "never-log" not in repr(snapshot)
    with pytest.raises(TypeError):
        snapshot["action"] = "changed"
    with pytest.raises(TypeError):
        snapshot["details"]["nested"][0]["safe"] = "changed"
    assert audit.events()[0]["action"] == "test"


def test_secret_names_are_validated_and_missing_secret_is_safe():
    store = SecretStore({"VALID_SECRET": "example-only"})
    assert store.get("VALID_SECRET") == "example-only"
    assert store.get("MISSING_SECRET") is None
    with pytest.raises(ValueError):
        store.get("../secret")


def test_authenticator_rejects_expired_tokens_and_never_trusts_mutable_roles():
    clock = Clock()
    auth = Authenticator("p" * 32, clock=clock)
    roles = {"user"}
    token = auth.issue("user-1", roles, ttl_seconds=1)
    roles.add("admin")
    assert auth.authenticate(token).roles == frozenset({"user"})
    clock.now += 1
    with pytest.raises(SecurityError):
        auth.authenticate(token)
