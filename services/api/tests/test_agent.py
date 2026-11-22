import tempfile
import unittest
from pathlib import Path
from services.api.security import ApprovalEngine,AuthContext,AuditLogger,EmergencyStop,Policy,PolicyEngine,RestrictedActionManager
from services.api.modules.agent.runtime import AgentError,AgentPlanner,BrowserInterface,ComputerControlInterface,ToolDefinition,ToolRegistry,ToolResult,build_agent
class AgentTests(unittest.TestCase):
 def setUp(self):
  self.audit=AuditLogger();self.policies=PolicyEngine()
  for name in ("filesystem.write","browser.navigate","computer.perform"):self.policies.register(Policy(f"agent.tool.{name}",frozenset({"user","admin"}),True,True))
  self.approvals=ApprovalEngine(policy_engine=self.policies);self.permissions=RestrictedActionManager(self.policies,self.approvals,EmergencyStop(self.audit),self.audit)
  self.context=AuthContext("alice",frozenset({"user"}));self.other=AuthContext("bob",frozenset({"user"}));self.temp=tempfile.TemporaryDirectory();self.tools=ToolRegistry()
  self.agent=build_agent(self.tools,self.permissions,self.temp.name,BrowserInterface(lambda _:"page body",lambda url:url),ComputerControlInterface(lambda action,args:{"action":action}))
 def tearDown(self):self.temp.cleanup()
 def test_planning_and_fail_closed(self):
  self.assertEqual(AgentPlanner().plan("alice","read file notes.txt").steps[0].tool_name,"filesystem.read")
  with self.assertRaises(AgentError):AgentPlanner().plan("alice","do something on my computer")
 def test_tool_allowlist_workspace_and_read_verification(self):
  self.tools.get("filesystem.write").handler({"path":"sub/a.txt","content":"hello"})
  self.assertEqual(self.tools.get("filesystem.read").handler({"path":"sub/a.txt"}).value,"hello")
  with self.assertRaises(AgentError):self.tools.get("filesystem.read").handler({"path":"../escape"})
  with self.assertRaises(AgentError):self.tools.get("shell.execute")
  with self.assertRaises(AgentError):self.tools.get("filesystem.read").handler({"path":"missing"})
 def test_sensitive_effect_requires_distinct_exact_approval_and_verifies(self):
  record=self.agent.submit(self.context,"write file output.txt with content: approved text");self.assertEqual(record.state,"awaiting_approval");self.assertFalse(Path(self.temp.name,"output.txt").exists())
  pending=record.observations[-1];grant=self.approvals.request("alice",pending["action"],pending["resource_id"])
  with self.assertRaises(Exception):self.approvals.decide(grant.approval_id,"alice",approved=True)
  self.approvals.decide(grant.approval_id,"reviewer",approved=True)
  result=self.agent.execute(self.context,record.task_id,grant.approval_id);self.assertEqual(result.state,"succeeded");self.assertEqual(Path(self.temp.name,"output.txt").read_text(),"approved text")
 def test_wrong_scope_and_owner_filtered_history(self):
  record=self.agent.submit(self.context,"write file no.txt with content: no");self.assertEqual(self.agent.history(self.other),[])
  with self.assertRaises(AgentError):self.agent.get(self.other,record.task_id)
  grant=self.approvals.request("alice",record.observations[-1]["action"],"different-resource");self.approvals.decide(grant.approval_id,"reviewer",approved=True)
  self.assertEqual(self.agent.execute(self.context,record.task_id,grant.approval_id).state,"failed");self.assertFalse(Path(self.temp.name,"no.txt").exists())
 def test_browser_read_only_and_navigation_sensitive(self):
  self.assertEqual(self.agent.submit(self.context,"inspect https://example.com").state,"succeeded")
  self.assertTrue(self.tools.get("browser.navigate").sensitive)
  with self.assertRaises(AgentError):self.tools.get("browser.navigate").handler({"url":"file:///etc/passwd"})
 def test_computer_actions_are_injected_and_bounded(self):
  self.assertEqual(self.tools.get("computer.perform").handler({"action":"click"}).value,{"action":"click"})
  with self.assertRaises(AgentError):self.tools.get("computer.perform").handler({"action":"shell"})
 def test_unverified_result_fails_task(self):
  tools=ToolRegistry();tools.register(ToolDefinition("filesystem.read","test",False,lambda _:ToolResult("x","not verified",False)))
  from services.api.modules.agent.runtime import AgentService
  self.assertEqual(AgentService(tools,self.permissions).submit(self.context,"read file x").state,"failed")
 def test_rejection_and_history(self):
  record=self.agent.submit(self.context,"write file rejected.txt with content: no");self.assertEqual(self.agent.reject(self.context,record.task_id).state,"rejected");self.assertEqual(self.agent.history(self.context)[0].task_id,record.task_id)
if __name__=="__main__":unittest.main()
