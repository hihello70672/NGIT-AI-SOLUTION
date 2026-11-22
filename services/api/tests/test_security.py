"""Security engine regression tests; run with PYTHONPATH=. python -m unittest discover -s services/api/tests."""
import unittest

from services.api.security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecretStore, SecurityError,
    error_payload,
)


class Clock:
    def __init__(self, now=1000.0):
        self.now = now
    def __call__(self):
        return self.now


class AuthenticatorTests(unittest.TestCase):
    def test_digest_only_issue_authenticate_revoke_and_expiry(self):
        clock = Clock()
        auth = Authenticator("x" * 32, clock=clock)
        token = auth.issue("u1", {"user"}, ttl_seconds=2)
        self.assertEqual(auth.authenticate(token).user_id, "u1")
        self.assertNotIn(token, auth._tokens)
        clock.now += 2
        with self.assertRaisesRegex(SecurityError, "Authentication required"):
            auth.authenticate(token)
        token = auth.issue("u1")
        auth.revoke(token)
        with self.assertRaises(SecurityError):
            auth.authenticate(token)

    def test_bad_pepper_and_bad_role_fail_closed(self):
        with self.assertRaises(ValueError):
            Authenticator("short")
        auth = Authenticator("x" * 32)
        with self.assertRaises(ValueError):
            auth.issue("u1", {"Admin"})


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.audit = AuditLogger()
        self.policy = PolicyEngine()
        self.policy.register(Policy("document.write", frozenset({"user"}), True, True))
        self.approvals = ApprovalEngine(clock=self.clock)
        self.stop = EmergencyStop(self.audit)
        self.manager = RestrictedActionManager(self.policy, self.approvals, self.stop, self.audit)
        self.alice = AuthContext("alice", frozenset({"user"}))

    def test_default_deny_rbac_owner_and_exact_resource(self):
        with self.assertRaises(SecurityError):
            self.policy.authorize(self.alice, "unknown")
        with self.assertRaises(SecurityError):
            self.policy.authorize(self.alice, "document.write", owner_id="bob")
        grant = self.approvals.request("alice", "document.write", "doc-1")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        with self.assertRaisesRegex(SecurityError, "approval"):
            self.manager.authorize(self.alice, "document.write", "doc-2", approval_id=grant.approval_id)
        self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)
        with self.assertRaises(SecurityError):
            self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)

    def test_approval_distinct_reviewer_expiry_and_rejection(self):
        grant = self.approvals.request("alice", "document.write", "doc-1", ttl_seconds=2)
        with self.assertRaises(SecurityError):
            self.approvals.decide(grant.approval_id, "alice", approved=True)
        self.approvals.decide(grant.approval_id, "reviewer", approved=False)
        self.assertFalse(self.approvals.consume(grant.approval_id, actor_user_id="alice", action="document.write", resource_id="doc-1"))
        expiring = self.approvals.request("alice", "document.write", "doc-1", ttl_seconds=1)
        self.clock.now += 1
        with self.assertRaises(SecurityError):
            self.approvals.decide(expiring.approval_id, "reviewer", approved=True)

    def test_emergency_stop_restricts_and_audits(self):
        grant = self.approvals.request("alice", "document.write", "doc-1")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.stop.engage("admin", "incident")
        with self.assertRaisesRegex(SecurityError, "temporarily disabled"):
            self.manager.authorize(self.alice, "document.write", "doc-1", approval_id=grant.approval_id)
        self.assertEqual(self.audit.events()[-1]["outcome"], "denied")
        self.stop.reset("admin")
        self.assertFalse(self.stop.stopped)

    def test_audit_redacts_nested_sensitive_keys_and_defends_internal_state(self):
        self.audit.record(action="test", details={"access_token": "do-not-log", "nested": {"api-key": "no", "safe": "yes"}})
        event = self.audit.events()[0]
        self.assertNotIn("do-not-log", repr(event))
        self.assertNotIn('"no"', repr(event))
        event["details"]["nested"]["safe"] = "tampered"
        self.assertEqual(self.audit.events()[0]["details"]["nested"]["safe"], "yes")
        self.audit.record(action="opaque", details={"label": "Bearer super-secret-token"})
        self.assertNotIn("super-secret-token", repr(self.audit.events()))

    def test_policy_rejects_invalid_restricted_and_role_configuration(self):
        with self.assertRaises(ValueError):
            PolicyEngine().register(Policy("action", frozenset({"user"}), restricted=True))
        with self.assertRaises(ValueError):
            PolicyEngine().register(Policy("good.action", frozenset({"Admin"})))

    def test_secret_names_are_validated_and_values_not_transformed(self):
        store = SecretStore({"VALID_SECRET_2": "example-only"})
        self.assertEqual(store.get("VALID_SECRET_2"), "example-only")
        with self.assertRaises(ValueError):
            store.get("bad-name")

    def test_error_payload_is_non_disclosing(self):
        payload = error_payload(SecurityError("forbidden", "Denied"), "req-1")
        self.assertEqual(payload["error"]["request_id"], "req-1")
        self.assertEqual(payload["error"]["details"], {})


if __name__ == "__main__":
    unittest.main()
