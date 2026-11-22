import tempfile
import unittest
from pathlib import Path
from services.api.security import (ApprovalEngine, AuthContext, AuditLogger, EmergencyStop, Policy, PolicyEngine, RestrictedActionManager)
from services.api.modules.agent.runtime import (AgentError, AgentPlanner, BrowserInterface, ComputerControlInterface, ToolDefinition, ToolRegistry, ToolResult, build_agent)

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.audit=AuditLogger();policies=PolicyEngine()
        for name in ("filesystem.write","browser.navigate","computer.perform"):policies.register(Policy(f"agent.tool.{name}",frozenset({"user","admin"}),approval_required=True,restricted=True))
        self.approvals=ApprovalEngine();self.permissions=RestrictedActionManager(policies,self.approvals,EmergencyStop(self.audit),self.audit)
        self.context=AuthContext("alice",frozenset({"user"}));self.other=AuthContext("bob",frozenset({"user"}))
        self.temp=tempfile.TemporaryDirectory();self.tools=ToolRegistry()
        self.agent=build_agent(self.tools,self.permissions,self.temp.name,BrowserInterface(reader=lambda _:"page text",navigator=lambda url:{"url":url}),ComputerControlInterface(lambda action,args:{"action":action}))
    def tearDown(self):self.temp.cleanup()
    def test_planner_is_explicit_and_rejects_ambiguous_goals(self):
        self.assertEqual(AgentPlanner().plan("alice","read file notes.txt").steps[0].tool_name,"filesystem.read")
        with self.assertRaises(AgentError):AgentPlanner().plan("alice","do something on my computer")
    def test_registry_rejects_duplicate_and_unknown_tools(self):
        registry=ToolRegistry();item=ToolDefinition("safe.tool","safe",False,lambda _:ToolResult("ok","ok",True));registry.register(item)
        with self.assertRaises(ValueError):registry.register(item)
        with self.assertRaises(AgentError):registry.get("unknown.tool")
    def test_workspace_read_and_escape_blocked(self):
        Path(self.temp.name,"hello.txt").write_text("hello",encoding="utf-8")
        self.assertEqual(self.tools.get("filesystem.read").handler({"path":"hello.txt"}).value,"hello")
        with self.assertRaises(AgentError):self.tools.get("filesystem.read").handler({"path":"../escape.txt"})
    def test_sensitive_write_pauses_then_uses_exact_one_time_approval(self):
        record=self.agent.submit(self.context,"write file result.txt with content: approved text")
        self.assertEqual(record.state,"awaiting_approval");self.assertFalse(Path(self.temp.name,"result.txt").exists())
        pending=next(x for x in record.observations if x["state"]=="approval_required")
        grant=self.approvals.request("alice",pending["action"],pending["resource_id"]);self.approvals.decide(grant.approval_id,"reviewer",approved=True)
        record.pending_approval_id=grant.approval_id
        done=self.agent.execute(self.context,record.task_id,grant.approval_id)
        self.assertEqual(done.state,"succeeded");self.assertEqual(Path(self.temp.name,"result.txt").read_text(),"approved text")
        self.assertEqual(self.agent.execute(self.context,record.task_id,grant.approval_id).state,"succeeded")
    def test_wrong_resource_approval_fails_without_side_effect(self):
        record=self.agent.submit(self.context,"write file denied.txt with content: no")
        pending=record.observations[-1];grant=self.approvals.request("alice",pending["action"],"different-resource");self.approvals.decide(grant.approval_id,"reviewer",approved=True)
        record.pending_approval_id=grant.approval_id
        self.assertEqual(self.agent.execute(self.context,record.task_id,grant.approval_id).state,"failed")
        self.assertFalse(Path(self.temp.name,"denied.txt").exists())
    def test_task_history_and_get_are_owner_scoped(self):
        record=self.agent.submit(self.context,"inspect https://example.com")
        self.assertEqual(record.state,"succeeded");self.assertEqual(self.agent.history(self.other),[])
        with self.assertRaises(AgentError):self.agent.get(self.other,record.task_id)
    def test_failed_verification_never_succeeds(self):
        from services.api.modules.agent.runtime import AgentPlan, AgentService, PlannedStep
        tools=ToolRegistry();tools.register(ToolDefinition("safe.verify","unverified",False,lambda _:ToolResult("value","not verified",False)))
        class Planner:
            def plan(self,owner,goal):return AgentPlan("task",owner,goal,(PlannedStep("safe.verify",{},"test"),),"now")
        self.assertEqual(AgentService(tools,self.permissions,Planner()).submit(self.context,"test").state,"failed")
    def test_browser_url_and_computer_adapter_fail_closed(self):
        with self.assertRaises(AgentError):self.tools.get("browser.inspect").handler({"url":"file:///etc/passwd"})
        with self.assertRaises(AgentError):ComputerControlInterface().perform({"action":"click"})

if __name__=="__main__":unittest.main()
