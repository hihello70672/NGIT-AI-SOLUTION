"""Additional adversarial regression tests for security boundaries."""

import pytest

from services.api.security import (
    ApprovalEngine,
    AuthContext,
    AuditLogger,
    Authenticator,
    EmergencyStop,
    Policy,
    PolicyEngine,
    RestrictedActionManager,
    SecretStore,
    SecurityError,
)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def test_secret_store_rejects_non_string_environment_values():
    with pytest.raises(ValueError):
        SecretStore({"VALID_SECRET": None}).get("VALID_SECRET")


def test_policy_unknown_role_and_unknown_action_are_denied():
    engine = PolicyEngine()
    engine.register(Policy("resource.read", frozenset({"reader"})))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("u", frozenset({"Reader"})), "resource.read")
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("u", frozenset({"reader"})), "resource.delete")


def test_approval_rejection_cannot_be_consumed_and_is_bound_to_exact_scope():
    approvals = ApprovalEngine()
    rejected = approvals.request("actor", "file.write", "file-1")
    approvals.decide(rejected.approval_id, "reviewer", approved=False)
    assert not approvals.consume(
        rejected.approval_id, actor_user_id="actor", action="file.write", resource_id="file-1"
    )
    grant = approvals.request("actor", "file.write", "file-1")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    assert not approvals.consume(
        grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file-2"
    )
    assert approvals.consume(
        grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file-1"
    )


def test_restricted_action_does_not_consume_approval_before_stop_check():
    audit = AuditLogger()
    policy = PolicyEngine()
    policy.register(Policy("file.write", frozenset({"editor"}), True, True))
    approvals = ApprovalEngine()
    grant = approvals.request("actor", "file.write", "file-1")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policy, approvals, stop, audit)
    caller = AuthContext("actor", frozenset({"editor"}))
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(caller, "file.write", "file-1", approval_id=grant.approval_id)
    stop.reset("admin")
    assert manager.authorize(caller, "file.write", "file-1", approval_id=grant.approval_id)


def test_audit_redacts_secrets_even_when_key_has_punctuation_or_nested_data():
    audit = AuditLogger()
    event = audit.record(
        action="credential.test",
        details={"api-key": "sensitive-value", "nested": [{"password_hash": "also-sensitive"}]},
    )
    assert "sensitive-value" not in repr(event)
    assert "also-sensitive" not in repr(event)


def test_expiration_boundary_is_denied():
    clock = Clock()
    auth = Authenticator("p" * 32, clock=clock)
    token = auth.issue("actor", {"user"}, ttl_seconds=1)
    clock.now += 1
    with pytest.raises(SecurityError):
        auth.authenticate(token)
    approvals = ApprovalEngine(clock=clock)
    approval = approvals.request("actor", "file.write", "file-1", ttl_seconds=1)
    approvals.decide(approval.approval_id, "reviewer", approved=True)
    clock.now += 1
    assert not approvals.consume(
        approval.approval_id, actor_user_id="actor", action="file.write", resource_id="file-1"
    )


def test_secret_lookup_only_accepts_environment_variable_names():
    store = SecretStore({"SAFE_SECRET": "value"})
    assert store.get("SAFE_SECRET") == "value"
    for name in ("", "MY-SECRET", "../secret", "A" * 127):
        with pytest.raises(ValueError):
            store.get(name)
