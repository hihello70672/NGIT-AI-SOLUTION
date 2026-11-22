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
            policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}), True, True))
        self.approvals = ApprovalEngine()
        self.permissions = RestrictedActionManager(policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"}))
        self.other = AuthContext("bob", frozenset({"user"}))
        self.temp = tempfile.TemporaryDirectory()
        self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.temp.name,
            BrowserInterface(lambda _: "page contents", lambda url: {"url": url}),
            ComputerControlInterface(lambda action, args: {"action": action}))

    def tearDown(self):
        self.temp.cleanup()

    def test_planner_is_explicit_and_refuses_ambiguous_goal(self):
        self.assertEqual(AgentPlanner().plan("alice", "read file notes.txt").steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError):
            AgentPlanner().plan("alice", "do something on my computer")

    def test_registry_rejects_duplicates_and_unknown_tools(self):
        registry = ToolRegistry()
        definition = ToolDefinition("safe.tool", "safe", False, lambda _: ToolResult(1, "ok", True))
        registry.register(definition)
        with self.assertRaises(ValueError):
            registry.register(definition)
        with self.assertRaises(AgentError):
            registry.get("unknown.tool")

    def test_filesystem_workspace_sandbox_and_read(self):
        Path(self.temp.name, "hello.txt").write_text("hello", encoding="utf-8")
        self.assertEqual(self.tools.get("filesystem.read").handler({"path": "hello.txt"}).value, "hello")
        with self.assertRaises(AgentError):
            self.tools.get("filesystem.read").handler({"path": "../escape.txt"})

    def test_sensitive_write_pauses_until_exact_one_time_approval(self):
        record = self.agent.submit(self.context, "write file result.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval")
        destination = Path(self.temp.name, "result.txt")
        self.assertFalse(destination.exists())
        pending = record.observations[-1]
        grant = self.approvals.request("alice", pending["action"], pending["resource_id"])
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        record.pending_approval_id = grant.approval_id
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "succeeded")
        self.assertEqual(destination.read_text(encoding="utf-8"), "approved text")
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "succeeded")

    def test_wrong_resource_approval_fails_closed(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = record.observations[-1]
        grant = self.approvals.request("alice", pending["action"], "different-resource")
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.execute(self.context, record.task_id, grant.approval_id).state, "failed")
        self.assertFalse(Path(self.temp.name, "denied.txt").exists())

    def test_observation_verification_and_owner_scoped_history(self):
        record = self.agent.submit(self.context, "inspect https://example.com")
        self.assertEqual(record.state, "succeeded")
        self.assertEqual(self.agent.history(self.other), [])
        with self.assertRaises(AgentError):
            self.agent.get(self.other, record.task_id)
        tools = ToolRegistry()
        tools.register(ToolDefinition("test.verify", "verification", False,
                                      lambda _: ToolResult("value", "unverified", False)))
        from services.api.modules.agent.runtime import AgentPlan, AgentService, PlannedStep
        class Planner:
            def plan(self, owner, goal):
                return AgentPlan("verify-task", owner, goal, (PlannedStep("test.verify", {}, "test"),), "now")
        self.assertEqual(AgentService(tools, self.permissions, Planner()).submit(self.context, "test").state, "failed")

    def test_browser_url_validation_and_computer_adapter_boundary(self):
        with self.assertRaises(AgentError):
            self.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})
        self.assertEqual(self.tools.get("computer.perform").handler({"action": "click"}).verified, True)
        with self.assertRaises(AgentError):
            ComputerControlInterface().perform({"action": "click"})

    def test_rejection_leaves_sensitive_side_effect_unperformed(self):
        record = self.agent.submit(self.context, "write file rejected.txt with content: never")
        self.assertEqual(self.agent.reject(self.context, record.task_id).state, "rejected")
        self.assertFalse(Path(self.temp.name, "rejected.txt").exists())


if __name__ == "__main__":
    unittest.main()
