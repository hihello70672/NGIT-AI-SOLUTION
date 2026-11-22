import tempfile
import unittest
from pathlib import Path
from services.api.security import (ApprovalEngine, AuthContext, AuditLogger, EmergencyStop, Policy,
    PolicyEngine, RestrictedActionManager)
from services.api.modules.agent.runtime import (AgentError, AgentPlanner, BrowserInterface,
    ComputerControlInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent)

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLogger(); policies = PolicyEngine()
        for name in ("filesystem.write", "browser.navigate", "computer.perform"):
            policies.register(Policy(f"agent.tool.{name}", frozenset({"user", "admin"}), True, True))
        self.approvals = ApprovalEngine()
        self.permissions = RestrictedActionManager(policies, self.approvals, EmergencyStop(self.audit), self.audit)
        self.context = AuthContext("alice", frozenset({"user"})); self.other = AuthContext("bob", frozenset({"user"}))
        self.temp = tempfile.TemporaryDirectory(); self.tools = ToolRegistry()
        self.agent = build_agent(self.tools, self.permissions, self.temp.name,
            BrowserInterface(lambda _: "page text", lambda url: {"url": url}),
            ComputerControlInterface(lambda action, _: {"action": action}))
    def tearDown(self): self.temp.cleanup()
    def test_plan_is_explicit_and_ambiguous_goal_fails_closed(self):
        self.assertEqual(AgentPlanner().plan("alice", "read file notes.txt").steps[0].tool_name, "filesystem.read")
        with self.assertRaises(AgentError): AgentPlanner().plan("alice", "do something on my computer")
    def test_registry_allowlist_and_duplicates(self):
        with self.assertRaises(ValueError): self.tools.register(self.tools.get("filesystem.read"))
        with self.assertRaises(AgentError): self.tools.get("shell.execute")
    def test_filesystem_bounds_and_verification(self):
        result = self.tools.get("filesystem.write").handler({"path": "hello.txt", "content": "hello"})
        self.assertTrue(result.verified)
        self.assertEqual(self.tools.get("filesystem.read").handler({"path": "hello.txt"}).value, "hello")
        with self.assertRaises(AgentError): self.tools.get("filesystem.read").handler({"path": "../escape"})
    def test_sensitive_write_requires_distinct_approval_and_exact_resume(self):
        record = self.agent.submit(self.context, "write file output.txt with content: approved text")
        self.assertEqual(record.state, "awaiting_approval")
        target = Path(self.temp.name, "output.txt"); self.assertFalse(target.exists())
        pending = record.observations[-1]
        grant = self.approvals.request("alice", pending["action"], pending["resource_id"])
        with self.assertRaises(Exception): self.approvals.decide(grant.approval_id, "alice", approved=True)
        self.approvals.decide(grant.approval_id, "reviewer", approved=True)
        done = self.agent.execute(self.context, record.task_id, grant.approval_id)
        self.assertEqual(done.state, "succeeded"); self.assertEqual(target.read_text(), "approved text")
        self.assertEqual(self.agent.history(self.context)[0].task_id, record.task_id)
    def test_wrong_scope_fails_closed(self):
        record = self.agent.submit(self.context, "write file denied.txt with content: no")
        pending = record.observations[-1]
        wrong = self.approvals.request("alice", pending["action"], "other-resource")
        self.approvals.decide(wrong.approval_id, "reviewer", approved=True)
        self.assertEqual(self.agent.execute(self.context, record.task_id, wrong.approval_id).state, "failed")
        self.assertFalse(Path(self.temp.name, "denied.txt").exists())
    def test_unverified_result_fails_task(self):
        self.tools.register(ToolDefinition("test.unverified", "test", False, lambda _: ToolResult("value", "not verified", False)))
        from services.api.modules.agent.runtime import AgentPlan, PlannedStep, AgentService
        class Planner:
            def plan(self, owner, goal): return AgentPlan("verify-task", owner, goal, (PlannedStep("test.unverified", {}, "test"),), "now")
        service = AgentService(self.tools, self.permissions, Planner())
        self.assertEqual(service.submit(self.context, "test").state, "failed")
    def test_browser_validation_and_computer_adapter(self):
        with self.assertRaises(AgentError): self.tools.get("browser.inspect").handler({"url": "file:///etc/passwd"})
        self.assertTrue(self.tools.get("computer.perform").handler({"action": "click"}).verified)
    def test_task_owner_scope_and_rejection(self):
        record = self.agent.submit(self.context, "write file rejected.txt with content: no")
        self.assertEqual(self.agent.history(self.other), [])
        with self.assertRaises(AgentError): self.agent.get(self.other, record.task_id)
        self.agent.reject(self.context, record.task_id)
        self.assertFalse(Path(self.temp.name, "rejected.txt").exists())

if __name__ == "__main__": unittest.main()
