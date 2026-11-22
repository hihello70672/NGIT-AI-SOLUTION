"""Security engine regression tests."""
import unittest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecretStore, SecurityError,
    error_payload,
)


class Clock:
    def __init__(self, now=1000): self.now = now
    def __call__(self): return self.now


class AuthenticatorTests(unittest.TestCase):
    def test_digest_only_issue_expiry_and_revocation(self):
        clock = Clock()
        auth = Authenticator("x" * 32, clock=clock)
        token = auth.issue("u1", {"user"}, ttl_seconds=2)
        self.assertNotIn(token, auth._tokens)
        self.assertEqual(auth.authenticate(token).user_id, "u1")
        auth.revoke(token)
        with self.assertRaises(SecurityError): auth.authenticate(token)
        token = auth.issue("u1", ttl_seconds=1)
        clock.now += 1
        with self.assertRaises(SecurityError): auth.authenticate(token)

    def test_invalid_roles_and_secret_strength(self):
        with self.assertRaises(ValueError): Authenticator("short")
        auth = Authenticator("x" * 32)
        with self.assertRaises(ValueError): auth.issue("u", {"Admin"})


class PolicyApprovalTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.audit = Clock(), AuditLogger()
        self.policies = PolicyEngine()
        self.policies.register(Policy("doc.write", frozenset({"user"}), True, True))
        self.approvals = ApprovalEngine(clock=self.clock)
        self.stop = EmergencyStop(self.audit)
        self.actions = RestrictedActionManager(self.policies, self.approvals, self.stop, self.audit)
        self.alice = AuthContext("alice", frozenset({"user"}))

    def test_deny_by_default_role_and_owner_checks(self):
        with self.assertRaises(SecurityError): self.policies.authorize(self.alice, "unknown")
        with self.assertRaises(SecurityError): self.policies.authorize(self.alice, "doc.write", owner_id="bob")
        self.assertEqual(self.policies.authorize(AuthContext("root", frozenset({"admin"})),
                                                  "doc.write", owner_id="bob").action, "doc.write")

    def test_distinct_approval_is_bound_single_use_and_expires(self):
        grant = self.approvals.request("alice", "doc.write", "doc-1", ttl_seconds=2)
        with self.assertRaises(SecurityError): self.approvals.decide(grant.approval_id, "alice", approved=True)
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertFalse(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="doc.write", resource_id="doc-2"))
        self.assertTrue(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="doc.write", resource_id="doc-1"))
        self.assertFalse(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="doc.write", resource_id="doc-1"))
        expiring = self.approvals.request("alice", "doc.write", "doc-3", ttl_seconds=1)
        self.approvals.decide(expiring.approval_id, "reviewer", approved=True)
        self.clock.now += 1
        self.assertFalse(self.approvals.consume(expiring.approval_id, actor_user_id="alice", action="doc.write", resource_id="doc-3"))

    def test_stop_switch_and_approval_are_fail_closed(self):
        grant = self.approvals.request("alice", "doc.write", "doc-1")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.stop.engage("admin", "incident")
        with self.assertRaises(SecurityError):
            self.actions.authorize(self.alice, "doc.write", "doc-1", approval_id=grant.approval_id)
        self.stop.reset("admin")
        self.actions.authorize(self.alice, "doc.write", "doc-1", approval_id=grant.approval_id)
        with self.assertRaises(SecurityError):
            self.actions.authorize(self.alice, "doc.write", "doc-1", approval_id=grant.approval_id)
        self.assertEqual(self.audit.events()[-1]["outcome"], "denied")

    def test_restricted_policy_requires_approval_and_safe_errors(self):
        with self.assertRaises(ValueError): self.policies.register(Policy("bad.action", frozenset({"user"}), restricted=True))
        payload = error_payload(SecurityError("forbidden", "Denied"), "req")
        self.assertEqual(payload["error"]["request_id"], "req")
        self.assertEqual(payload["error"]["details"], {})


class AuditAndSecretsTests(unittest.TestCase):
    def test_audit_redaction_and_immutable_event_snapshots(self):
        audit = AuditLogger()
        event = audit.record(action="test", details={"access_token": "never", "nested": {"api-key": "no", "safe": "yes"}})
        self.assertNotIn("never", repr(event))
        self.assertNotIn('"no"', repr(event))
        event["details"]["nested"]["safe"] = "tampered"
        snapshot = audit.events()
        with self.assertRaises(TypeError):
            snapshot[0]["details"]["nested"]["safe"] = "also tampered"
        self.assertEqual(audit.events()[0]["details"]["nested"]["safe"], "yes")
        audit.record(action="opaque", details={"label": "Bearer abcd-token-value"})
        self.assertNotIn("abcd-token-value", repr(audit.events()))

    def test_secret_name_validation_and_safe_error_payload(self):
        store = SecretStore({"VALID_SECRET_2": "example-only"})
        self.assertEqual(store.get("VALID_SECRET_2"), "example-only")
        with self.assertRaises(ValueError): store.get("bad-name")
        payload = error_payload(SecurityError("forbidden", "Denied"), "req")
        self.assertEqual(payload["error"]["request_id"], "req")
        self.assertEqual(payload["error"]["details"], {})


if __name__ == "__main__": unittest.main()
