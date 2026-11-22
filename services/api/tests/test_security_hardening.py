"""Adversarial regression tests for security-engine boundaries."""
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


def test_secret_store_rejects_invalid_names_and_non_string_values():
    with pytest.raises(ValueError):
        SecretStore({"BAD": None}).get("BAD")
    for name in ("", "MY-SECRET", "../secret", "A" * 127):
        with pytest.raises(ValueError):
            SecretStore().get(name)


def test_policy_requires_exact_types_and_unknown_action_denies():
    engine = PolicyEngine()
    with pytest.raises(ValueError):
        engine.register(Policy("unsafe.action", frozenset({"user"}), restricted=True))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("user", frozenset({"user"})), "not.registered")
    engine.register(Policy("record.read", frozenset({"reader"})))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("user", frozenset({"Reader"})), "record.read")


def test_approval_rejection_expiry_scope_and_separation_are_closed():
    clock = Clock()
    approvals = ApprovalEngine(clock=clock)
    rejected = approvals.request("actor", "file.write", "file-1")
    approvals.decide(rejected.approval_id, "reviewer", approved=False)
    assert not approvals.consume(rejected.approval_id, actor_user_id="actor", action="file.write", resource_id="file-1")
    grant = approvals.request("actor", "file.write", "file-1", ttl_seconds=1)
    with pytest.raises(SecurityError):
        approvals.decide(grant.approval_id, "actor", approved=True)
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    assert not approvals.consume(grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file-2")
    clock.now += 1
    assert not approvals.consume(grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file-1")


def test_restricted_gate_checks_stop_before_consuming_approval_and_audits_denial():
    audit = AuditLogger()
    policies = PolicyEngine()
    policies.register(Policy("file.write", frozenset({"editor"}), True, True))
    approvals = ApprovalEngine()
    grant = approvals.request("actor", "file.write", "file-1")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policies, approvals, stop, audit)
    context = AuthContext("actor", frozenset({"editor"}))
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(context, "file.write", "file-1", approval_id=grant.approval_id)
    stop.reset("admin")
    assert manager.authorize(context, "file.write", "file-1", approval_id=grant.approval_id).action == "file.write"
    with pytest.raises(SecurityError):
        manager.authorize(context, "file.write", "file-1", approval_id=grant.approval_id)
    assert [event["outcome"] for event in audit.events()] == ["denied", "authorized", "denied"]


def test_authenticator_does_not_accept_bool_ttl_or_mutable_role_context():
    auth = Authenticator("p" * 32)
    with pytest.raises(ValueError):
        auth.issue("user", {"user"}, ttl_seconds=True)
    token = auth.issue("user", {"user"})
    context = auth.authenticate(token)
    with pytest.raises(AttributeError):
        context.roles.add("admin")


def test_audit_nested_sensitive_keys_are_redacted_and_snapshots_immutable():
    audit = AuditLogger()
    event = audit.record(action="test", details={"nested": [{"api-key": "secret-value"}], "safe": "value"})
    assert "secret-value" not in repr(event)
    snapshot = audit.events()[0]
    with pytest.raises(TypeError):
        snapshot["details"]["safe"] = "changed"
    assert audit.events()[0]["details"]["safe"] == "value"
