"""Conservative Personal Agent planner and approval-gated capability execution."""
from __future__ import annotations
import importlib, os, re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from uuid import uuid4
from services.api.security import AuthContext, RestrictedActionManager, SecurityError
class AgentError(ValueError):
    """Safe machine-readable agent failure."""
    def __init__(self,code:str,message:str): super().__init__(message); self.code,self.message=code,message
@dataclass(frozen=True)
class PlannedStep: tool_name:str; arguments:Mapping[str,Any]; description:str
@dataclass(frozen=True)
class AgentPlan: task_id:str; owner_id:str; goal:str; steps:tuple[PlannedStep,...]; created_at:str
@dataclass(frozen=True)
class ToolResult: value:Any; observation:str; verified:bool
@dataclass
class TaskRecord:
    task_id:str; owner_id:str; goal:str; state:str; created_at:str; updated_at:str
    plan:list[dict[str,Any]]=field(default_factory=list); observations:list[dict[str,Any]]=field(default_factory=list)
    result:Any=None; error:str|None=None; pending_approval_id:str|None=None
@dataclass(frozen=True)
class ToolDefinition: name:str; description:str; sensitive:bool; handler:Callable[[Mapping[str,Any]],ToolResult]
class ToolRegistry:
    """Explicit allowlist for agent capabilities."""
    def __init__(self): self._tools={}
    def register(self,definition):
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}",definition.name): raise ValueError("invalid tool name")
        if definition.name in self._tools: raise ValueError("tool already registered")
        self._tools[definition.name]=definition
    def get(self,name):
        try:return self._tools[name]
        except KeyError as exc:raise AgentError("tool_not_found","Requested tool is not available") from exc
    def list(self):return [{"name":t.name,"description":t.description,"sensitive":t.sensitive} for t in sorted(self._tools.values(),key=lambda x:x.name)]
class BrowserInterface:
    """Injected browser boundary; adapter must enforce network security."""
    def __init__(self,reader=None,navigator=None):self.reader=reader or (lambda url:f"Browser adapter unavailable for {urlparse(url).netloc}");self.navigator=navigator
    @staticmethod
    def _url(value):
        if not isinstance(value,str) or len(value)>2048:raise AgentError("invalid_arguments","A valid HTTP(S) URL is required")
        parsed=urlparse(value)
        if parsed.scheme not in {"http","https"} or not parsed.hostname or parsed.username or parsed.password:raise AgentError("invalid_arguments","A valid HTTP(S) URL is required")
        return value
    def inspect(self,args):
        value=self.reader(self._url(args.get("url")))
        if not isinstance(value,str):raise AgentError("tool_failed","Browser adapter returned an invalid observation")
        return ToolResult(value[:20000],"Browser page inspected",True)
    def navigate(self,args):
        url=self._url(args.get("url"))
        if self.navigator is None:raise AgentError("tool_unavailable","Browser navigation adapter is not configured")
        return ToolResult(self.navigator(url),"Browser navigation completed",True)
class FilesystemInterface:
    """Workspace-bound UTF-8 text access, not an OS sandbox."""
    MAX_BYTES=1_000_000
    def __init__(self,root):self.root=Path(root).expanduser().resolve();self.root.mkdir(parents=True,exist_ok=True)
    def resolve(self,value):
        if not isinstance(value,str) or not value or len(value)>1024:raise AgentError("invalid_arguments","A relative filesystem path is required")
        path=(self.root/value).resolve()
        if path!=self.root and self.root not in path.parents:raise AgentError("path_forbidden","Filesystem path escapes configured workspace")
        return path
    def read(self,args):
        path=self.resolve(args.get("path"))
        try:
            if not path.is_file() or path.stat().st_size>self.MAX_BYTES:raise AgentError("invalid_arguments","File is missing or exceeds the read limit")
            content=path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:raise AgentError("invalid_arguments","Only UTF-8 text files can be read") from exc
        return ToolResult(content,f"Read {path.relative_to(self.root)}",True)
    def write(self,args):
        path=self.resolve(args.get("path"));content=args.get("content")
        if not isinstance(content,str) or len(content.encode("utf-8"))>self.MAX_BYTES:raise AgentError("invalid_arguments","Text content is required and limited to 1 MiB")
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding="utf-8");verified=path.read_text(encoding="utf-8")==content
        return ToolResult({"path":str(path.relative_to(self.root)),"bytes":len(content.encode("utf-8"))},"File write verified" if verified else "File write verification failed",verified)
class ComputerControlInterface:
    """Delegates enumerated actions to an injected adapter."""
    ACTIONS={"screenshot","click","type","keypress"}
    def __init__(self,adapter=None):self.adapter=adapter
    def perform(self,args):
        action=args.get("action")
        if action not in self.ACTIONS:raise AgentError("invalid_arguments","Unsupported computer action")
        if self.adapter is None:raise AgentError("tool_unavailable","Computer-control adapter is not configured")
        return ToolResult(self.adapter(action,args),f"Computer action {action} completed",True)
class AgentPlanner:
    """Deterministic one-step planning; ambiguous goals fail closed."""
    def plan(self,owner_id,goal):
        if not isinstance(owner_id,str) or not owner_id or not isinstance(goal,str) or not goal.strip() or len(goal)>4000:raise AgentError("invalid_goal","A non-empty goal of at most 4000 characters is required")
        text=goal.strip();match=re.fullmatch(r"(?:read|show)\s+(?:file\s+)?(.+)",text,re.I)
        if match:step=PlannedStep("filesystem.read",{"path":match.group(1).strip()},"Read a workspace file")
        else:
            match=re.fullmatch(r"(?:write|create)(?:\s+file)?\s+(.+?)\s+with\s+content:\s*([\s\S]+)",text,re.I)
            if match:step=PlannedStep("filesystem.write",{"path":match.group(1).strip(),"content":match.group(2)},"Write a workspace file")
            else:
                match=re.fullmatch(r"inspect\s+(https?://\S+)",text,re.I)
                if match:step=PlannedStep("browser.inspect",{"url":match.group(1)},"Inspect a web page")
                else:raise AgentError("plan_unavailable","Could not safely turn this goal into an explicit tool plan")
        return AgentPlan(str(uuid4()),owner_id,text,(step,),datetime.now(timezone.utc).isoformat())
class AgentService:
    def __init__(self,tools,permissions,planner=None):self.tools,self.permissions,self.planner=tools,permissions,planner or AgentPlanner();self._records={};self._plans={};self._lock=RLock()
    @staticmethod
    def _now():return datetime.now(timezone.utc).isoformat()
    def submit(self,context,goal):
        plan=self.planner.plan(context.user_id,goal);record=TaskRecord(plan.task_id,context.user_id,plan.goal,"accepted",plan.created_at,self._now(),[{"tool_name":s.tool_name,"arguments":dict(s.arguments),"description":s.description} for s in plan.steps])
        with self._lock:self._records[record.task_id]=record;self._plans[record.task_id]=plan
        return self.execute(context,record.task_id)
    def execute(self,context,task_id,approval_id=None):
        with self._lock:
            record=self._owned(context,task_id);plan=self._plans.get(task_id)
            if plan is None:raise AgentError("task_not_found","Task was not found")
            if record.state in {"succeeded","failed","rejected"}:return record
            if record.state=="running":raise AgentError("task_running","Task is already running")
            start=0
            if record.state=="awaiting_approval":
                pending=next((o for o in record.observations if o.get("state")=="approval_required"),None)
                if not approval_id or pending is None:return record
                if record.pending_approval_id and approval_id!=record.pending_approval_id:record.state,record.error,record.updated_at="failed","approval_scope_mismatch",self._now();return record
                try:self.permissions.authorize(context,pending["action"],pending["resource_id"],approval_id=approval_id)
                except SecurityError as exc:record.state,record.error,record.updated_at="failed",exc.code,self._now();return record
                record.observations=[o for o in record.observations if o.get("state")!="approval_required"];record.pending_approval_id=None;start=pending["step"]
            record.state,record.updated_at="running",self._now()
        for index in range(start,len(plan.steps)):
            step=plan.steps[index];tool=self.tools.get(step.tool_name);action=f"agent.tool.{tool.name}";resource=f"{task_id}:{index}"
            if tool.sensitive:
                try:self.permissions.authorize(context,action,resource)
                except SecurityError as exc:
                    if exc.code=="approval_required":
                        with self._lock:record.state,record.updated_at="awaiting_approval",self._now();record.observations.append({"step":index,"state":"approval_required","action":action,"resource_id":resource})
                        return record
                    with self._lock:record.state,record.error,record.updated_at="failed",exc.code,self._now();return record
            try:
                result=tool.handler(step.arguments)
                if not isinstance(result,ToolResult):raise AgentError("tool_failed","Tool returned an invalid result")
                with self._lock:
                    record.observations.append({"step":index,"tool_name":tool.name,"observation":result.observation,"verified":result.verified,"value":result.value})
                    if not result.verified:record.state,record.error,record.updated_at="failed","verification_failed",self._now();return record
                    record.result=result.value;record.updated_at=self._now()
            except AgentError as exc:
                with self._lock:record.state,record.error,record.updated_at="failed",exc.code,self._now();return record
            except Exception:
                with self._lock:record.state,record.error,record.updated_at="failed","tool_failed",self._now();return record
        with self._lock:record.state,record.updated_at="succeeded",self._now();return record
    def reject(self,context,task_id):
        with self._lock:
            record=self._owned(context,task_id)
            if record.state!="awaiting_approval":raise AgentError("invalid_task_state","Task is not awaiting approval")
            record.state,record.error,record.updated_at="rejected","approval_rejected",self._now();return record
    def _owned(self,context,task_id):
        record=self._records.get(task_id)
        if record is None or record.owner_id!=context.user_id:raise AgentError("task_not_found","Task was not found")
        return record
    def get(self,context,task_id):
        with self._lock:return self._owned(context,task_id)
    def history(self,context,limit=50):
        if isinstance(limit,bool) or not 1<=limit<=100:raise AgentError("invalid_limit","Limit must be between 1 and 100")
        with self._lock:return sorted((r for r in self._records.values() if r.owner_id==context.user_id),key=lambda r:r.created_at,reverse=True)[:limit]
def _load_adapter(spec):
    if not isinstance(spec,str) or ":" not in spec:raise ValueError("adapter must use module:callable syntax")
    module,attribute=spec.split(":",1);candidate=getattr(importlib.import_module(module),attribute)
    if not callable(candidate):raise ValueError("configured adapter is not callable")
    return candidate
def build_agent(tools,permissions,workspace,browser=None,computer=None):
    browser=browser or BrowserInterface(_load_adapter(os.environ["NGIT_AGENT_BROWSER_READER"]) if os.getenv("NGIT_AGENT_BROWSER_READER") else None,_load_adapter(os.environ["NGIT_AGENT_BROWSER_NAVIGATOR"]) if os.getenv("NGIT_AGENT_BROWSER_NAVIGATOR") else None)
    computer=computer or ComputerControlInterface(_load_adapter(os.environ["NGIT_AGENT_COMPUTER_ADAPTER"]) if os.getenv("NGIT_AGENT_COMPUTER_ADAPTER") else None);fs=FilesystemInterface(workspace)
    for d in (ToolDefinition("browser.inspect","Read-only HTTP(S) page inspection",False,browser.inspect),ToolDefinition("browser.navigate","Approval-gated HTTP(S) navigation",True,browser.navigate),ToolDefinition("filesystem.read","Read UTF-8 text from workspace",False,fs.read),ToolDefinition("filesystem.write","Approval-gated workspace text write",True,fs.write),ToolDefinition("computer.perform","Approval-gated injected computer action",True,computer.perform)):tools.register(d)
    return AgentService(tools,permissions)
def public_record(record):return {"task_id":record.task_id,"goal":record.goal,"state":record.state,"created_at":record.created_at,"updated_at":record.updated_at,"plan":record.plan,"observations":record.observations,"result":record.result,"error":record.error,"pending_approval_id":record.pending_approval_id}
__all__=["AgentError","AgentPlan","AgentPlanner","AgentService","BrowserInterface","ComputerControlInterface","FilesystemInterface","PlannedStep","TaskRecord","ToolDefinition","ToolRegistry","ToolResult","build_agent","public_record"]
