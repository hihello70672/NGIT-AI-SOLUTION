"""Security engine regression tests; run with pytest or unittest discovery."""
import unittest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecretStore, SecurityError, error_payload,
)


class Clock:
    def __init__(self, now=1000.0): self.now = now
    def __call__(self): return self.now


class AuthenticatorTests(unittest.TestCase):
    def test_digest_only_issue_authenticate_revoke_and_expiry(self):
        clock = Clock()
        auth = Authenticator("x" * 32, clock=clock)
        token = auth.issue("u1", {"user"}, ttl_seconds=2)
        self.assertEqual(auth.authenticate(token).user_id, "u1")
        self.assertNotIn(token, auth._tokens)
        clock.now += 2
        with self.assertRaises(SecurityError): auth.authenticate(token)
        token = auth.issue("u1")
        auth.revoke(token)
        with self.assertRaises(SecurityError): auth.authenticate(token)

    def test_bad_pepper_role_and_ttl_fail_closed(self):
        with self.assertRaises(ValueError): Authenticator("short")
        auth = Authenticator("x" * 32)
        for kwargs in ({"roles": {"Admin"}}, {"ttl_seconds": True}, {"ttl_seconds": 86401}):
            with self.assertRaises(ValueError): auth.issue("u1", **kwargs)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.audit = Clock(), AuditLogger()
        self.policies = PolicyEngine()
        self.policies.register(Policy("document.write", frozenset({"user"}), True, True))
        self.approvals = ApprovalEngine(clock=self.clock)
        self.stop = EmergencyStop(self.audit)
        self.manager = RestrictedActionManager(self.policies, self.approvals, self.stop, self.audit)
        self.alice = AuthContext("alice", frozenset({"user"}))

    def test_deny_by_default_role_and_owner_checks(self):
        for fn in (lambda: self.policies.authorize(self.alice, "unknown"),
                   lambda: self.policies.authorize(self.alice, "document.write", owner_id="bob")):
            with self.assertRaises(SecurityError): fn()
        admin = AuthContext("admin", frozenset({"admin"}))
        self.assertEqual(self.policies.authorize(admin, "document.write", owner_id="bob").action, "document.write")

    def test_approval_is_distinct_exact_resource_one_time_and_expiring(self):
        grant = self.approvals.request("alice", "document.write", "doc-1", ttl_seconds=2)
        with self.assertRaises(SecurityError): self.approvals.decide(grant.approval_id, "alice", approved=True)
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertFalse(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-2"))
        self.assertTrue(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-1"))
        self.assertFalse(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-1"))
        expiring = self.approvals.request("alice", "document.write", "doc-3", ttl_seconds=1)
        self.clock.now += 1
        with self.assertRaises(SecurityError): self.approvals.decide(expiring.approval_id, "reviewer", approved=True)

    def test_stop_denial_audit_and_reset(self):
        grant = self.approvals.request("alice", "document.write", "doc-1")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.stop.engage("admin", "incident")
        with self.assertRaisesRegex(SecurityError, "temporarily disabled"):
            self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)
        self.assertEqual(self.audit.events()[-1]["outcome"], "denied")
        self.stop.reset("admin")
        # Denial above does not consume the grant; successful authorization consumes it.
        self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)
        with self.assertRaises(SecurityError):
            self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)

    def test_restricted_default_policy_must_require_approval(self):
        with self.assertRaises(ValueError):
            self.policies.register(Policy("unsafe.action", frozenset({"user"}), restricted=True))


class AuditAndSecretTests(unittest.TestCase):
    def test_audit_recursively_redacts_and_returns_copies(self):
        audit = AuditLogger()
        event = audit.record(action="test", details={"access_token": "do-not-log", "nested": {"api-key": "no", "safe": "yes"}})
        self.assertNotIn("do-not-log", repr(event))
        self.assertNotIn('"no"', repr(event))
        event["details"]["nested"]["safe"] = "tampered"
        self.assertEqual(audit.events()[0]["details"]["nested"]["safe"], "yes")

    def test_secret_names_are_validated_and_values_not_transformed(self):
        store = SecretStore({"VALID_SECRET_2": "example-only"})
        self.assertEqual(store.get("VALID_SECRET_2"), "example-only")
        with self.assertRaises(ValueError): store.get("bad-name")

    def test_error_payload_does_not_disclose_details(self):
        payload = error_payload(SecurityError("forbidden", "Denied"), "req-1")
        self.assertEqual(payload["error"]["request_id"], "req-1")
        self.assertEqual(payload["error"]["details"], {})


if __name__ == "__main__":
    unittest.main()
