"""Security engine regression tests: run with python -m pytest -q tests/test_security.py."""
import threading

import pytest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop, Policy, PolicyEngine,
    RestrictedActionManager, SecretStore, SecurityError, error_payload,
)


class Clock:
    def __init__(self, now=1000):
        self.now = now

    def __call__(self):
        return self.now


def test_tokens_are_opaque_expiring_revocable_and_bind_server_roles():
    clock = Clock()
    auth = Authenticator("x" * 32, clock=clock)
    token = auth.issue("user-1", {"user"}, ttl_seconds=2)
    assert token not in auth._tokens
    assert auth.authenticate(token).roles == frozenset({"user"})
    auth.revoke(token)
    with pytest.raises(SecurityError):
        auth.authenticate(token)
    token = auth.issue("user-1", {"user"}, ttl_seconds=1)
    clock.now += 1
    with pytest.raises(SecurityError):
        auth.authenticate(token)
    with pytest.raises(ValueError):
        auth.issue("user", {"Admin"})


def test_policy_is_deny_by_default_role_checked_and_owner_scoped():
    engine = PolicyEngine()
    engine.register(Policy("document.write", frozenset({"editor"})))
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("a", frozenset({"viewer"})), "document.write")
    with pytest.raises(SecurityError):
        engine.authorize(AuthContext("a", frozenset({"editor"})), "document.write", owner_id="b")
    assert engine.authorize(AuthContext("a", frozenset({"editor"})), "document.write", owner_id="a").action == "document.write"
    with pytest.raises(ValueError):
        engine.register(Policy("restricted.no_approval", frozenset({"admin"}), restricted=True))


def test_approval_enforces_separation_exact_scope_expiry_and_single_use():
    clock = Clock()
    approvals = ApprovalEngine(clock=clock)
    grant = approvals.request("alice", "document.write", "doc-1", ttl_seconds=2)
    with pytest.raises(SecurityError):
        approvals.decide(grant.approval_id, "alice", approved=True)
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    assert not approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-2")
    assert approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-1")
    assert not approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-1")
    expired = approvals.request("alice", "document.write", "doc-3", ttl_seconds=1)
    approvals.decide(expired.approval_id, "reviewer", approved=True)
    clock.now += 1
    assert not approvals.consume(expired.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-3")


def test_restricted_action_stop_and_approval_denials_are_audited():
    audit, clock = AuditLogger(), Clock()
    policies = PolicyEngine()
    policies.register(Policy("document.write", frozenset({"editor"}), True, True))
    approvals = ApprovalEngine(clock=clock)
    stop = EmergencyStop(audit)
    manager = RestrictedActionManager(policies, approvals, stop, audit)
    caller = AuthContext("alice", frozenset({"editor"}))
    with pytest.raises(SecurityError):
        manager.authorize(caller, "document.write", "doc")
    grant = approvals.request("alice", "document.write", "doc")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        manager.authorize(caller, "document.write", "doc", approval_id=grant.approval_id)
    assert audit.events()[-1]["outcome"] == "denied"
    stop.reset("admin")
    with pytest.raises(SecurityError):
        manager.authorize(caller, "document.write", "doc", approval_id=grant.approval_id)


def test_audit_redacts_secrets_and_returns_deeply_immutable_snapshots():
    audit = AuditLogger()
    event = audit.record(action="example", details={"access_token": "must-not-appear", "nested": {"safe": [1]}})
    assert "must-not-appear" not in repr(event)
    with pytest.raises(TypeError):
        audit.events()[0]["details"]["nested"]["safe"] = "tamper"
    audit.record(action="example", details={"api-key": "secret-value"})
    assert "secret-value" not in repr(audit.events())


def test_audit_concurrent_writes_are_not_lost():
    audit = AuditLogger()
    threads = [threading.Thread(target=lambda n=n: audit.record(action="test", details={"n": n})) for n in range(100)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(audit.events()) == 100


def test_secret_names_and_safe_error_envelope():
    assert SecretStore({"VALID_SECRET_2": "example-only"}).get("VALID_SECRET_2") == "example-only"
    with pytest.raises(ValueError):
        SecretStore({}).get("not-valid")
    error = error_payload(SecurityError("forbidden", "Denied"), "request-1")
    assert error["error"]["request_id"] == "request-1"
    assert error["error"]["details"] == {}
    assert "secret" not in repr(error).lower()


def test_approval_consumption_is_atomic_under_concurrency():
    approvals = ApprovalEngine()
    grant = approvals.request("actor", "file.write", "file")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    outcomes = []
    threads = [threading.Thread(target=lambda: outcomes.append(approvals.consume(
        grant.approval_id, actor_user_id="actor", action="file.write", resource_id="file"))) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count(True) == 1


def test_emergency_stop_audits_engage_and_reset():
    audit = AuditLogger()
    stop = EmergencyStop(audit)
    stop.engage("admin", "incident")
    with pytest.raises(SecurityError):
        stop.check()
    stop.reset("admin")
    stop.check()
    assert [event["action"] for event in audit.events()] == ["emergency_stop.engaged", "emergency_stop.reset"]
