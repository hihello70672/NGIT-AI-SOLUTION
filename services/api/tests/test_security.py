"""Security engine regression tests; run with PYTHONPATH=services/api python -m unittest discover -s services/api/tests."""
import unittest

from security import (
    ApprovalEngine, AuthContext, Authenticator, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager, SecurityError, SecretStore,
    error_payload,
)


class Clock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


class AuthenticatorTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.auth = Authenticator("x" * 32, clock=self.clock)

    def test_issue_authenticate_and_revoke(self):
        token = self.auth.issue("user-1", {"user"})
        self.assertEqual(self.auth.authenticate(token).user_id, "user-1")
        self.auth.revoke(token)
        with self.assertRaises(SecurityError):
            self.auth.authenticate(token)

    def test_expiry_and_invalid_tokens_fail_closed(self):
        token = self.auth.issue("user-1", ttl_seconds=2)
        self.clock.now += 2
        with self.assertRaisesRegex(SecurityError, "Authentication required"):
            self.auth.authenticate(token)
        for value in (None, "", "unissued"):
            with self.assertRaises(SecurityError):
                self.auth.authenticate(value)

    def test_pepper_requirement_and_environment_secret(self):
        with self.assertRaises(ValueError):
            Authenticator("short")
        self.assertEqual(SecretStore({"SAMPLE_SECRET": "not-printed"}).get("SAMPLE_SECRET"), "not-printed")


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger()
        self.policies = PolicyEngine({
            "read": Policy("read", frozenset({"user", "admin"})),
            "write": Policy("write", frozenset({"admin"}), restricted=True, approval_required=True),
        })
        self.approvals = ApprovalEngine()
        self.stop = EmergencyStop(self.audit)
        self.manager = RestrictedActionManager(self.policies, self.approvals, self.stop, self.audit)
        self.admin = AuthContext("alice", frozenset({"admin"}))

    def test_default_deny_rbac_and_owner_isolation(self):
        with self.assertRaises(SecurityError):
            self.policies.authorize(self.admin, "unknown")
        with self.assertRaises(SecurityError):
            self.policies.authorize(AuthContext("bob", frozenset({"user"})), "read", owner_id="alice")
        self.assertEqual(self.policies.authorize(self.admin, "read", owner_id="alice").action, "read")

    def test_approval_needs_distinct_actor_and_is_bound_and_single_use(self):
        approval = self.approvals.request("alice", "write", "resource")
        with self.assertRaises(SecurityError):
            self.approvals.decide(approval.approval_id, "alice", approved=True)
        self.approvals.decide(approval.approval_id, "bob", approved=True)
        self.assertFalse(self.approvals.consume(approval.approval_id, actor_user_id="alice", action="write", resource_id="other"))
        self.assertTrue(self.approvals.consume(approval.approval_id, actor_user_id="alice", action="write", resource_id="resource"))
        self.assertFalse(self.approvals.consume(approval.approval_id, actor_user_id="alice", action="write", resource_id="resource"))

    def test_restricted_action_requires_approval_and_honors_emergency_stop(self):
        with self.assertRaises(SecurityError) as caught:
            self.manager.authorize(self.admin, "write", "r")
        self.assertEqual(caught.exception.code, "approval_required")
        approval = self.approvals.request("alice", "write", "r")
        self.approvals.decide(approval.approval_id, "security-reviewer", approved=True)
        self.stop.engage("admin-1", "incident response")
        with self.assertRaises(SecurityError) as caught:
            self.manager.authorize(self.admin, "write", "r", approval_id=approval.approval_id)
        self.assertEqual(caught.exception.code, "emergency_stop")
        self.stop.reset("admin-1")
        approval = self.approvals.request("alice", "write", "r")
        self.approvals.decide(approval.approval_id, "reviewer", approved=True)
        self.manager.authorize(self.admin, "write", "r", approval_id=approval.approval_id)

    def test_audit_redacts_sensitive_fields_and_captures_denial(self):
        self.audit.record(action="test", details={"access_token": "do-not-log", "safe": "ok"})
        self.assertNotIn("access_token", self.audit.events()[0]["details"])
        self.assertNotIn("do-not-log", repr(self.audit.events()))
        with self.assertRaises(SecurityError):
            self.manager.authorize(AuthContext("user", frozenset({"user"})), "write", "r")
        self.assertEqual(self.audit.events()[-1]["outcome"], "denied")

    def test_error_envelope_is_safe(self):
        payload = error_payload(SecurityError("forbidden", "No"), "req-1")
        self.assertEqual(payload["error"]["request_id"], "req-1")
        self.assertEqual(payload["error"]["details"], {})


if __name__ == "__main__":
    unittest.main()
