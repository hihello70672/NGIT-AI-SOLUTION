import tempfile
import unittest
from pathlib import Path

from services.api.security import (ApprovalEngine, AuthContext, AuditLogger, EmergencyStop, Policy,
                                   PolicyEngine, RestrictedActionManager, SecurityError)
from services.api.modules.agent.runtime import (AgentError, AgentPlanner, AgentService, BrowserInterface,
    ComputerControlInterface, FilesystemInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger()
        policies = PolicyEngine()
        policies.register(Policy("agent.tool.filesystem.write", frozenset({"user", "admin"}),
                                 approval_required=True, restricted=True))
        policies.register(Policy("agent.tool.browser.navigate", frozenset({"user", "admin"}),
                                 approval_required=True, restricted=True))
        policies.register(Policy("agent.tool.computer.perform", frozenset({"user", "admin"}),
                                 approval_required=True, restricted=True))
        self.approvals = ApprovalEngine()
        self.permissions = RestrictedActionManager(policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"}))
        self.other = AuthContext("bob", frozenset({"user"}))
        self.temp = tempfile.TemporaryDirectory()
        self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.temp.name,
                                 browser=BrowserInterface(reader=lambda url: "page text", navigator=lambda url: {"url": url}),
                                 computer=ComputerControlInterface(lambda action, args: {"action": action}))

    def tearDown(self):
        self.temp.cleanup()

    def test_planner_is_explicit_and_rejects_ambiguous_goals(self):
        plan = AgentPlanner().plan("alice", "read file notes.txt")
        self.assertEqual(plan.steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError):
            AgentPlanner().plan("alice", "do something on my computer")

    def test_registry_rejects_duplicate_and_unknown_tools(self):
        registry = ToolRegistry()
        tool = ToolDefinition("safe.tool", "safe", False, lambda args: ToolResult("ok", "ok", True))
        registry.register(tool)
        with self.assertRaises(ValueError):
            registry.register(tool)
        with self.assertRaises(AgentError):
            registry.get("unknown.tool")

    def test_read_file_is_sandboxed_and_verified(self):
        path = Path(self.temp.name) / "hello.txt"
        path.write_text("hello", encoding="utf-8")
        result = self.agent.tools.get("filesystem.read").handler({"path": "hello.txt"})
        self.assertEqual(result.value, "hello")
        with self.assertRaises(AgentError):
            self.agent.tools.get("filesystem.read").handler({"path": "../escape.txt"})

    def test_sensitive_write_waits_for_different_approver_then_runs_once(self):
        record = self.agent.submit(self.context, "write file result.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval")
        self.assertFalse((Path(self.temp.name) / "result.txt").exists())
        pending = next(item for item in record.observations if item["state"] == "approval_required")
        approval = self.approvals.request("alice", pending["action"], pending["resource_id"])
        self.approvals.decide(approval.approval_id, "reviewer", approved=True)
        done = self.agent.approve_and_resume(self.context, record.task_id, approval.approval_id)
        self.assertEqual(done.state, "succeeded")
        self.assertEqual((Path(self.temp.name) / "result.txt").read_text(), "approved text")
        self.assertEqual(len([x for x in done.observations if x.get("verified")]), 1)

    def test_rejected_or_wrong_resource_approval_never_executes(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = next(item for item in record.observations if item["state"] == "approval_required")
        wrong = self.approvals.request("alice", pending["action"], "different-resource")
        self.approvals.decide(wrong.approval_id, "reviewer", approved=True)
        finished = self.agent.approve_and_resume(self.context, record.task_id, wrong.approval_id)
        self.assertEqual(finished.state, "failed")
        self.assertFalse((Path(self.temp.name) / "denied.txt").exists())

    def test_owner_scoped_history_and_task_lookup(self):
        record = self.agent.submit(self.context, "inspect https://example.com")
        self.assertEqual(record.state, "succeeded")
        self.assertEqual(len(self.agent.history(self.other)), 0)
        with self.assertRaises(AgentError):
            self.agent.get(self.other, record.task_id)

    def test_browser_url_validation_and_observation(self):
        result = self.agent.tools.get("browser.inspect").handler({"url": "https://example.com"})
        self.assertTrue(result.verified)
        with self.assertRaises(AgentError):
            self.agent.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})

    def test_missing_computer_adapter_fails_closed(self):
        iface = ComputerControlInterface()
        with self.assertRaises(AgentError):
            iface.perform({"action": "click"})


if __name__ == "__main__":
    unittest.main()
