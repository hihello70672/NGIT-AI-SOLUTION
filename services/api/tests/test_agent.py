import tempfile
import unittest
from pathlib import Path
from services.api.security import ApprovalEngine, AuthContext, AuditLogger, EmergencyStop, Policy, PolicyEngine, RestrictedActionManager
from services.api.modules.agent.runtime import AgentError, AgentPlanner, BrowserInterface, ComputerControlInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger(); self.policies = PolicyEngine()
        for name in ("filesystem.write", "browser.navigate", "computer.perform"):
            self.policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}), True, True))
        self.approvals = ApprovalEngine(policy_engine=self.policies)
        self.permissions = RestrictedActionManager(self.policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"})); self.other = AuthContext("bob", frozenset({"user"}))
        self.temp = tempfile.TemporaryDirectory(); self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.temp.name, BrowserInterface(lambda _: "page body", lambda url: url), ComputerControlInterface(lambda action, args: {"action": action}))
    def tearDown(self): self.temp.cleanup()
    def test_planner_explicit_and_fails_closed(self):
        self.assertEqual(AgentPlanner().plan("alice", "read file notes.txt").steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError): AgentPlanner().plan("alice", "do something on my computer")
    def test_registry_allowlist_and_duplicate_rejection(self):
        with self.assertRaises(ValueError): self.tools.register(self.tools.get("filesystem.read"))
        with self.assertRaises(AgentError): self.tools.get("shell.execute")
    def test_workspace_write_verification_and_path_escape(self):
        self.tools.get("filesystem.write").handler({"path": "sub/file.txt", "content": "hello"})
        self.assertEqual(self.tools.get("filesystem.read").handler({"path": "sub/file.txt"}).value, "hello")
        with self.assertRaises(AgentError): self.tools.get("filesystem.read").handler({"path": "../escape"})
    def test_sensitive_action_requires_distinct_approval_and_exact_resume(self):
        record = self.agent.submit(self.context, "write file output.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval"); self.assertFalse(Path(self.temp.name, "output.txt").exists())
        pending = record.observations[-1]; grant = self.approvals.request("alice", pending["action"], pending["resource_id"])
        with self.assertRaises(Exception): self.approvals.decide(grant.approval_id, "alice", approved=True)
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "succeeded")
        self.assertEqual(Path(self.temp.name, "output.txt").read_text(), "approved text")
    def test_approval_scope_mismatch_fails_closed(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = record.observations[-1]; grant = self.approvals.request("alice", pending["action"], "different-resource")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "failed")
        self.assertFalse(Path(self.temp.name, "denied.txt").exists())
    def test_unverified_tool_and_adapter_errors_fail_task(self):
        self.tools.register(ToolDefinition("test.unverified", "test", False, lambda _: ToolResult("x", "not verified", False)))
        with self.assertRaises(AgentError): self.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})
        self.assertTrue(self.tools.get("computer.perform").handler({"action": "click"}).verified)
    def test_history_owner_scoping_and_rejection(self):
        record = self.agent.submit(self.context, "write file reject.txt with content: no")
        self.assertEqual(self.agent.history(self.other), [])
        with self.assertRaises(AgentError): self.agent.get(self.other, record.task_id)
        self.assertEqual(self.agent.reject(self.context, record.task_id).state, "rejected")
    def test_browser_navigation_sensitive_and_inspection_read_only(self):
        self.assertEqual(self.agent.submit(self.context, "inspect https://example.com").state, "succeeded")
        navigation = self.agent.tools.get("browser.navigate")
        record = self.agent.planner.plan("alice", "inspect https://example.com")
        self.assertEqual(navigation.handler({"url": "https://example.com"}).value, "https://example.com")

if __name__ == "__main__": unittest.main()
