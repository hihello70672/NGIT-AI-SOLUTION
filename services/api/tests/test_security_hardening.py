"""Adversarial regression tests for security-engine boundaries."""
import threading
import pytest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecretStore, SecurityError,
)

class Clock:
    def __init__(self): self.now = 100.0
    def __call__(self): return self.now

def test_secret_store_rejects_invalid_names_and_non_string_values():
    with pytest.raises(ValueError): SecretStore({"BAD": None}).get("BAD")
    for name in ("", "MY-SECRET", "../secret", "A" * 127):
        with pytest.raises(ValueError): SecretStore().get(name)

def test_policy_validation_and_unknown_action_fail_closed():
    engine = PolicyEngine()
    with pytest.raises(ValueError): engine.register(Policy("restricted.action", frozenset({"user"}), restricted=True))
    with pytest.raises(SecurityError): engine.authorize(AuthContext("actor", frozenset({"user"})), "unregistered.action")

def test_approval_rejects_owner_and_roleless_reviewer():
    policies = PolicyEngine(); policies.register(Policy("agent.approval.decide", frozenset({"admin"})))
    engine = ApprovalEngine(policy_engine=policies); grant = engine.request("owner", "file.write", "file-1")
    with pytest.raises(SecurityError): engine.decide(grant.approval_id, "owner", approved=True, approver_roles=frozenset({"admin"}))
    with pytest.raises(SecurityError): engine.decide(grant.approval_id, "reviewer", approved=True, approver_roles=frozenset({"user"}))
    assert engine.get(grant.approval_id).status == "pending"

def test_approval_scope_expiry_and_atomic_single_consumption():
    clock = Clock(); engine = ApprovalEngine(clock=clock)
    grant = engine.request("owner", "file.write", "file-1", ttl_seconds=2)
    engine.decide(grant.approval_id, "reviewer", approved=True)
    assert not engine.consume(grant.approval_id, actor_user_id="owner", action="file.write", resource_id="file-2")
    outcomes = []
    threads = [threading.Thread(target=lambda: outcomes.append(engine.consume(grant.approval_id, actor_user_id="owner", action="file.write", resource_id="file-1"))) for _ in range(16)]
    [thread.start() for thread in threads]; [thread.join() for thread in threads]
    assert outcomes.count(True) == 1
    expired = engine.request("owner", "file.write", "file-2", ttl_seconds=1)
    engine.decide(expired.approval_id, "reviewer", approved=True); clock.now += 2
    assert not engine.consume(expired.approval_id, actor_user_id="owner", action="file.write", resource_id="file-2")

def test_audit_nested_secret_redaction_and_immutable_snapshot():
    audit = AuditLogger()
    event = audit.record(action="example", details={"nested": [{"api-key": "never-log-this"}], "safe": "value"})
    assert "never-log-this" not in repr(event)
    snapshot = audit.events()[0]
    with pytest.raises(TypeError): snapshot["details"]["safe"] = "changed"
    assert audit.events()[0]["details"]["safe"] == "value"

def test_stop_precedes_approval_consumption_and_denials_are_audited():
    audit = AuditLogger(); policies = PolicyEngine()
    policies.register(Policy("file.write", frozenset({"editor"}), approval_required=True, restricted=True))
    approvals = ApprovalEngine(); grant = approvals.request("owner", "file.write", "file-1")
    approvals.decide(grant.approval_id, "reviewer", approved=True)
    stop = EmergencyStop(audit); manager = RestrictedActionManager(policies, approvals, stop, audit)
    caller = AuthContext("owner", frozenset({"editor"})); stop.engage("admin", "incident")
    with pytest.raises(SecurityError): manager.authorize(caller, "file.write", "file-1", approval_id=grant.approval_id)
    assert approvals.get(grant.approval_id).status == "approved"
    stop.reset("admin")
    manager.authorize(caller, "file.write", "file-1", approval_id=grant.approval_id)
    with pytest.raises(SecurityError): manager.authorize(caller, "file.write", "file-1", approval_id=grant.approval_id)
    assert [event["outcome"] for event in audit.events() if event["action"] == "file.write"] == ["denied", "authorized", "denied"]

def test_authentication_ttl_and_roles_are_validated_and_revocable():
    auth = Authenticator("p" * 32)
    with pytest.raises(ValueError): auth.issue("user", {"user"}, ttl_seconds=True)
    token = auth.issue("user", {"user"}); context = auth.authenticate(token)
    with pytest.raises(AttributeError): context.roles.add("admin")
    auth.revoke(token)
    with pytest.raises(SecurityError): auth.authenticate(token)
