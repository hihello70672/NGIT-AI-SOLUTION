import tempfile
import unittest
from pathlib import Path
from services.api.security import (ApprovalEngine, AuthContext, AuditLogger, EmergencyStop, Policy,
    PolicyEngine, RestrictedActionManager)
from services.api.modules.agent.runtime import (AgentError, AgentPlanner, BrowserInterface,
    ComputerControlInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent)

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger()
        policies = PolicyEngine()
        for name in ("filesystem.write", "browser.navigate", "computer.perform"):
            policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}),
                                     approval_required=True, restricted=True))
        self.approvals = ApprovalEngine()
        self.permissions = RestrictedActionManager(policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"}))
        self.other = AuthContext("bob", frozenset({"user"}))
        self.temp = tempfile.TemporaryDirectory()
        self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.temp.name,
            BrowserInterface(reader=lambda url: "page text", navigator=lambda url: {"url": url}),
            ComputerControlInterface(lambda action, args: {"action": action}))

    def tearDown(self): self.temp.cleanup()

    def test_planner_is_explicit_and_rejects_ambiguous_goals(self):
        self.assertEqual(AgentPlanner().plan("alice", "read file notes.txt").steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError): AgentPlanner().plan("alice", "do something on my computer")

    def test_registry_rejects_duplicate_and_unknown_tools(self):
        registry = ToolRegistry()
        item = ToolDefinition("safe.tool", "safe", False, lambda args: ToolResult("ok", "ok", True))
        registry.register(item)
        with self.assertRaises(ValueError): registry.register(item)
        with self.assertRaises(AgentError): registry.get("unknown.tool")

    def test_read_is_sandboxed(self):
        (Path(self.temp.name) / "hello.txt").write_text("hello", encoding="utf-8")
        self.assertEqual(self.tools.get("filesystem.read").handler({"path": "hello.txt"}).value, "hello")
        with self.assertRaises(AgentError): self.tools.get("filesystem.read").handler({"path": "../escape.txt"})

    def test_sensitive_write_requires_different_approver_and_executes_after_grant(self):
        record = self.agent.submit(self.context, "write file result.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval")
        self.assertFalse((Path(self.temp.name) / "result.txt").exists())
        pending = next(item for item in record.observations if item["state"] == "approval_required")
        grant = self.approvals.request("alice", pending["action"], pending["resource_id"])
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        done = self.agent.approve_and_resume(self.context, record.task_id, grant.approval_id)
        self.assertEqual(done.state, "succeeded")
        self.assertEqual((Path(self.temp.name) / "result.txt").read_text(), "approved text")

    def test_wrong_resource_grant_never_executes(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = next(item for item in record.observations if item["state"] == "approval_required")
        grant = self.approvals.request("alice", pending["action"], "different-resource")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.approve_and_resume(self.context, record.task_id, grant.approval_id).state, "failed")
        self.assertFalse((Path(self.temp.name) / "denied.txt").exists())

    def test_owner_scoped_history(self):
        record = self.agent.submit(self.context, "inspect https://example.com")
        self.assertEqual(record.state, "succeeded")
        self.assertEqual(self.agent.history(self.other), [])
        with self.assertRaises(AgentError): self.agent.get(self.other, record.task_id)

    def test_browser_validates_url(self):
        self.assertEqual(self.tools.get("browser.inspect").handler({"url": "https://example.com"}).value, "page text")
        with self.assertRaises(AgentError): self.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})

    def test_missing_computer_adapter_fails_closed(self):
        with self.assertRaises(AgentError): ComputerControlInterface().perform({"action": "click"})

if __name__ == "__main__": unittest.main()
