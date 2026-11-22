"""Process-local security primitives for NGIT's modular API.

Tokens, approvals, stop state and audit events are process-local. Run one
worker until approved shared persistence replaces these primitives.
"""
from __future__ import annotations
import copy, hashlib, hmac, os, re, secrets, threading, time
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping

class SecurityError(Exception):
    """Expected security rejection with a safe machine code."""
    def __init__(self, code: str, message: str): super().__init__(message); self.code, self.message = code, message

@dataclass(frozen=True)
class AuthContext:
    user_id: str
    roles: frozenset[str] = frozenset()
    token_id: str = ""

@dataclass(frozen=True)
class Policy:
    action: str
    roles: frozenset[str]
    approval_required: bool = False
    restricted: bool = False

class SecretStore:
    """Environment-backed secret lookup; values are never logged."""
    def __init__(self, environ: Mapping[str,str] | None=None): self._environ=os.environ if environ is None else environ
    def get(self,name:str)->str|None:
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,126}",name): raise ValueError("invalid secret name")
        value=self._environ.get(name)
        if value is not None and not isinstance(value,str): raise ValueError("secret values must be strings")
        return value

class Authenticator:
    """Opaque random bearer tokens; only keyed token digests are retained."""
    def __init__(self,pepper:str|None=None,*,clock:Callable[[],float]=time.time):
        self._pepper=pepper if pepper is not None else SecretStore().get("AUTH_TOKEN_PEPPER")
        if not isinstance(self._pepper,str) or len(self._pepper.encode())<32: raise ValueError("AUTH_TOKEN_PEPPER must be configured and at least 32 bytes")
        self._clock,self._lock,self._tokens=clock,threading.RLock(),{}
    def _digest(self,token:str)->str: return hmac.new(self._pepper.encode(),token.encode(),hashlib.sha256).hexdigest()
    def issue(self,user_id:str,roles:set[str]|frozenset[str]=frozenset(),*,ttl_seconds:int=3600)->str:
        if not isinstance(user_id,str) or not user_id or len(user_id)>256: raise ValueError("invalid token issue parameters")
        if isinstance(ttl_seconds,bool) or not isinstance(ttl_seconds,int) or not 1<=ttl_seconds<=86400: raise ValueError("invalid token issue parameters")
        if not isinstance(roles,(set,frozenset)) or any(not isinstance(r,str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}",r) for r in roles): raise ValueError("invalid token roles")
        token=secrets.token_urlsafe(32); context=AuthContext(user_id,frozenset(roles),secrets.token_urlsafe(12))
        with self._lock:
            now=self._clock(); self._tokens={k:v for k,v in self._tokens.items() if v[1]>now}; self._tokens[self._digest(token)]=(context,now+ttl_seconds)
        return token
    def authenticate(self,token:str|None)->AuthContext:
        if not isinstance(token,str) or not token or len(token)>512: raise SecurityError("unauthenticated","Authentication required")
        key=self._digest(token)
        with self._lock:
            item=self._tokens.get(key)
            if item is None or item[1]<=self._clock(): self._tokens.pop(key,None); raise SecurityError("unauthenticated","Authentication required")
            return item[0]
    def revoke(self,token:str)->None:
        if isinstance(token,str) and len(token)<=512:
            with self._lock:self._tokens.pop(self._digest(token),None)

class AuditLogger:
    """Thread-safe redacted audit sink with immutable event snapshots."""
    _forbidden={"password","token","secret","credential","prompt","authorization","cookie","apikey"}
    def __init__(self):self._lock,self._events=threading.RLock(),[]
    @classmethod
    def _safe(cls,value:Any,depth:int=0)->Any:
        if depth>8:return "[TRUNCATED]"
        if isinstance(value,Mapping):
            out={}
            for key,item in value.items():
                text=str(key); norm=re.sub(r"[^a-z0-9]","",text.lower())
                if any(word.replace("_","") in norm for word in cls._forbidden):continue
                out[text[:128]]=cls._safe(item,depth+1)
            return out
        if isinstance(value,(list,tuple)):return [cls._safe(x,depth+1) for x in value[:100]]
        if value is None or isinstance(value,(bool,int,float)):return value
        if isinstance(value,str):return "[REDACTED]" if len(value)>=32 and re.fullmatch(r"[A-Za-z0-9_./+=-]+",value) else value[:512]
        return type(value).__name__
    def record(self,*,action:str,actor_user_id:str|None=None,resource_type:str|None=None,resource_id:str|None=None,request_id:str|None=None,outcome:str="success",details:Mapping[str,Any]|None=None)->dict[str,Any]:
        if not isinstance(action,str) or not action or len(action)>128:raise ValueError("invalid audit action")
        event={"action":action,"actor_user_id":self._safe(actor_user_id),"resource_type":self._safe(resource_type),"resource_id":self._safe(resource_id),"request_id":self._safe(request_id),"outcome":self._safe(outcome)[:64],"occurred_at":datetime.now(timezone.utc).isoformat(),"details":self._safe(details or {})}
        with self._lock:self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)
    def events(self)->tuple[Mapping[str,Any],...]:
        def freeze(v):
            if isinstance(v,dict):return MappingProxyType({k:freeze(i) for k,i in v.items()})
            if isinstance(v,list):return tuple(freeze(i) for i in v)
            return v
        with self._lock:return tuple(freeze(copy.deepcopy(x)) for x in self._events)

class PolicyEngine:
    """Allow-list RBAC and ownership authorization; unknown actions deny."""
    def __init__(self,policies:Mapping[str,Policy]|None=None):
        self._policies={}
        for p in (policies or {}).values():self.register(p)
    @staticmethod
    def _validate(p:Policy)->None:
        if not isinstance(p,Policy) or not isinstance(p.action,str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,126}",p.action):raise ValueError("invalid policy action")
        if not isinstance(p.roles,frozenset) or any(not isinstance(r,str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}",r) for r in p.roles):raise ValueError("invalid policy roles")
        if not isinstance(p.approval_required,bool) or not isinstance(p.restricted,bool):raise ValueError("invalid policy flags")
        if p.restricted and not p.approval_required:raise ValueError("restricted policies must require approval")
    def register(self,p:Policy)->None:
        self._validate(p)
        if p.action in self._policies:raise ValueError("policy action must be unique")
        self._policies[p.action]=p
    def get(self,action:str)->Policy|None:return self._policies.get(action)
    def authorize(self,context:AuthContext,action:str,*,owner_id:str|None=None)->Policy:
        if not isinstance(context,AuthContext) or not context.user_id:raise SecurityError("unauthenticated","Authentication required")
        p=self._policies.get(action)
        if p is None:raise SecurityError("forbidden","Action is not permitted")
        if owner_id is not None and owner_id!=context.user_id and "admin" not in context.roles:raise SecurityError("forbidden","Resource access is not permitted")
        if not p.roles.intersection(context.roles):raise SecurityError("forbidden","Action is not permitted")
        return p

@dataclass
class Approval:
    approval_id:str
    actor_user_id:str
    action:str
    resource_id:str
    expires_at:float
    status:str="pending"
    approver_user_id:str|None=None

class ApprovalEngine:
    """Bound, expiring approvals with separation of duties and atomic use."""
    def __init__(self,*,clock:Callable[[],float]=time.time):self._clock,self._lock,self._approvals=clock,threading.RLock(),{}
    def request(self,actor_user_id:str,action:str,resource_id:str,*,ttl_seconds:int=600)->Approval:
        if not all(isinstance(x,str) and x and len(x)<=256 for x in (actor_user_id,action,resource_id)):raise ValueError("invalid approval request")
        if isinstance(ttl_seconds,bool) or not isinstance(ttl_seconds,int) or not 1<=ttl_seconds<=3600:raise ValueError("invalid approval request")
        item=Approval(secrets.token_urlsafe(18),actor_user_id,action,resource_id,self._clock()+ttl_seconds)
        with self._lock:self._approvals[item.approval_id]=item
        return copy.deepcopy(item)
    def get(self,approval_id:str)->Approval|None:
        with self._lock:
            item=self._approvals.get(approval_id);return copy.deepcopy(item) if item else None
    def decide(self,approval_id:str,approver_user_id:str,*,approved:bool)->Approval:
        if not isinstance(approved,bool) or not isinstance(approver_user_id,str) or not approver_user_id:raise ValueError("invalid approval decision")
        with self._lock:
            item=self._approvals.get(approval_id)
            if item is None or item.expires_at<=self._clock() or item.status!="pending":raise SecurityError("approval_invalid","Approval is missing, expired, or already decided")
            if approver_user_id==item.actor_user_id:raise SecurityError("forbidden","A different approver is required")
            item.status="approved" if approved else "rejected";item.approver_user_id=approver_user_id
            return copy.deepcopy(item)
    def consume(self,approval_id:str,*,actor_user_id:str,action:str,resource_id:str)->bool:
        with self._lock:
            item=self._approvals.get(approval_id)
            if not item or item.status!="approved" or item.expires_at<=self._clock():return False
            if (item.actor_user_id,item.action,item.resource_id)!=(actor_user_id,action,resource_id):return False
            item.status="consumed";return True

class EmergencyStop:
    def __init__(self,audit:AuditLogger):self._audit,self._lock,self._stopped=audit,threading.RLock(),False
    @property
    def stopped(self):
        with self._lock:return self._stopped
    def engage(self,actor_user_id:str,reason:str):
        if not isinstance(actor_user_id,str) or not actor_user_id or not isinstance(reason,str) or not reason or len(reason)>256:raise ValueError("actor and bounded reason are required")
        with self._lock:self._stopped=True
        self._audit.record(action="emergency_stop.engaged",actor_user_id=actor_user_id,details={"reason":reason})
    def reset(self,actor_user_id:str):
        if not isinstance(actor_user_id,str) or not actor_user_id:raise ValueError("actor is required")
        with self._lock:self._stopped=False
        self._audit.record(action="emergency_stop.reset",actor_user_id=actor_user_id)
    def check(self):
        if self.stopped:raise SecurityError("emergency_stop","Restricted actions are temporarily disabled")

class RestrictedActionManager:
    """Single-use approval gate, immediately before a protected side effect."""
    def __init__(self,policies:PolicyEngine,approvals:ApprovalEngine,stop:EmergencyStop,audit:AuditLogger):self._policies,self._approvals,self._stop,self._audit=policies,approvals,stop,audit
    def authorize(self,context:AuthContext,action:str,resource_id:str,*,owner_id:str|None=None,approval_id:str|None=None,request_id:str|None=None)->Policy:
        try:
            p=self._policies.authorize(context,action,owner_id=owner_id)
            if p.restricted:self._stop.check()
            if p.approval_required and not self._approvals.consume(approval_id or "",actor_user_id=context.user_id,action=action,resource_id=resource_id):raise SecurityError("approval_required","A valid approval is required")
        except SecurityError as exc:
            self._audit.record(action=action if isinstance(action,str) else "unknown",actor_user_id=getattr(context,"user_id",None),resource_id=resource_id,request_id=request_id,outcome="denied",details={"error_code":exc.code});raise
        self._audit.record(action=action,actor_user_id=context.user_id,resource_id=resource_id,request_id=request_id,outcome="authorized")
        return p

def create_default_security():
    """Build default process-local security engines for the API entrypoint."""
    authenticator=Authenticator(SecretStore().get("AUTH_TOKEN_PEPPER"));audit=AuditLogger();policies=PolicyEngine()
    policies.register(Policy("profile.read",frozenset({"user","admin"})))
    policies.register(Policy("admin.users.manage",frozenset({"admin"}),True,True))
    policies.register(Policy("agent.approval.decide",frozenset({"admin"})))
    policies.register(Policy("admin.approvals.decide",frozenset({"admin"})))
    approvals=ApprovalEngine();stop=EmergencyStop(audit);actions=RestrictedActionManager(policies,approvals,stop,audit)
    return authenticator,policies,approvals,audit,stop,actions

def error_payload(error:SecurityError,request_id:str|None=None)->dict[str,Any]:return {"error":{"code":error.code,"message":error.message,"request_id":request_id,"details":{}}}

__all__=["Approval","ApprovalEngine","AuthContext","Authenticator","AuditLogger","EmergencyStop","Policy","PolicyEngine","RestrictedActionManager","SecretStore","SecurityError","create_default_security","error_payload"]
