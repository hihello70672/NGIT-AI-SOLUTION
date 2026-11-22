import tempfile
import unittest
from pathlib import Path
from services.api.security import (ApprovalEngine, AuthContext, AuditLogger, EmergencyStop,
    Policy, PolicyEngine, RestrictedActionManager)
from services.api.modules.agent.runtime import (AgentError, AgentPlanner, BrowserInterface,
    ComputerControlInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger()
        policies = PolicyEngine()
        for name in ("filesystem.write", "browser.navigate", "computer.perform"):
            policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}), True, True))
        self.approvals = ApprovalEngine()
        self.permissions = RestrictedActionManager(policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"}))
        self.other = AuthContext("bob", frozenset({"user"}))
        self.tmp = tempfile.TemporaryDirectory()
        self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.tmp.name,
            BrowserInterface(lambda _: "page text", lambda url: {"url": url}),
            ComputerControlInterface(lambda action, args: {"action": action}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_planner_explicit_and_ambiguous_fails_closed(self):
        self.assertEqual(AgentPlanner().plan("alice", "read file notes.txt").steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError):
            AgentPlanner().plan("alice", "do something on my computer")

    def test_registry_rejects_duplicate_and_unknown(self):
        registry = ToolRegistry()
        item = ToolDefinition("safe.tool", "safe", False, lambda _: ToolResult(1, "ok", True))
        registry.register(item)
        with self.assertRaises(ValueError): registry.register(item)
        with self.assertRaises(AgentError): registry.get("unknown.tool")

    def test_filesystem_workspace_boundaries_and_verification(self):
        Path(self.tmp.name, "hello.txt").write_text("hello", encoding="utf-8")
        self.assertEqual(self.tools.get("filesystem.read").handler({"path": "hello.txt"}).value, "hello")
        with self.assertRaises(AgentError): self.tools.get("filesystem.read").handler({"path": "../escape"})

    def test_sensitive_write_pauses_until_exact_one_time_approval(self):
        record = self.agent.submit(self.context, "write file out.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval")
        path = Path(self.tmp.name, "out.txt")
        self.assertFalse(path.exists())
        pending = record.observations[-1]
        grant = self.approvals.request("alice", pending["action"], pending["resource_id"])
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        resumed = self.agent.execute(self.context, record.task_id, grant.approval_id)
        self.assertEqual(resumed.state, "succeeded")
        self.assertEqual(path.read_text(encoding="utf-8"), "approved text")
        self.agent.execute(self.context, record.task_id, grant.approval_id)
        self.assertEqual(path.read_text(encoding="utf-8"), "approved text")

    def test_wrong_resource_approval_fails_closed(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = record.observations[-1]
        grant = self.approvals.request("alice", pending["action"], "different-resource")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "failed")
        self.assertFalse(Path(self.tmp.name, "denied.txt").exists())

    def test_verification_failure_never_succeeds(self):
        self.tools.register(ToolDefinition("test.unverified", "test", False,
            lambda _: ToolResult("value", "not verified", False)))
        from services.api.modules.agent.runtime import AgentPlan, AgentService, PlannedStep
        class Planner:
            def plan(self, owner, goal): return AgentPlan("verify-task", owner, goal,
                (PlannedStep("test.unverified", {}, "test"),), "now")
        agent = AgentService(self.tools, self.permissions, Planner())
        self.assertEqual(agent.submit(self.context, "test").state, "failed")

    def test_browser_url_validation_and_computer_adapter_boundary(self):
        with self.assertRaises(AgentError): self.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})
        self.assertTrue(self.tools.get("computer.perform").handler({"action": "click"}).verified)
        with self.assertRaises(AgentError): ComputerControlInterface().perform({"action": "click"})

    def test_owner_scoped_history_and_rejection_has_no_side_effect(self):
        record = self.agent.submit(self.context, "write file rejected.txt with content: no")
        self.assertEqual(self.agent.history(self.other), [])
        self.agent.reject(self.context, record.task_id)
        self.assertFalse(Path(self.tmp.name, "rejected.txt").exists())


if __name__ == "__main__": unittest.main()
