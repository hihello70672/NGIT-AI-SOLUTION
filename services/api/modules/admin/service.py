"""Administration services backed by NGIT's database and security engine."""
from __future__ import annotations
import re
from typing import Any
from services.api.security import AuthContext, AuditLogger, PolicyEngine, Policy, RestrictedActionManager

class AdminError(ValueError):
    """Invalid administrative operation or resource."""

class AdminService:
    """Policy-gated administration. Identity is always supplied by auth context."""
    def __init__(self,database:Any,policies:PolicyEngine,actions:RestrictedActionManager,audit:AuditLogger):
        self.database,self.policies,self.actions,self.audit=database,policies,actions,audit
    def _authorize(self,context:AuthContext,action:str,resource_id:str="")->None:
        policy=self.policies.authorize(context,action)
        if policy.restricted:self.actions.authorize(context,action,resource_id)
    @staticmethod
    def _rows(cursor:Any)->list[dict[str,Any]]:
        names=[item.name if hasattr(item,"name") else item[0] for item in cursor.description or ()]
        return [dict(zip(names,row)) for row in cursor.fetchall()]
    def _query(self,sql:str,params:tuple=(),caller:str|None=None,fetch:bool=True)->list[dict[str,Any]]:
        with self.database.connection(caller) as conn:
            cursor=conn.execute(sql,params)
            return self._rows(cursor) if fetch else []
    def list_resource(self,context:AuthContext,kind:str,limit:int=100,offset:int=0,query:str="")->list[dict[str,Any]]:
        if isinstance(limit,bool) or not 1<=limit<=100 or isinstance(offset,bool) or offset<0:raise AdminError("invalid pagination")
        specs={"users":("admin.users.read","SELECT id,email,display_name,status,created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s"),"roles":("admin.roles.read","SELECT id,name,description FROM roles ORDER BY name LIMIT %s OFFSET %s"),"models":("admin.models.read","SELECT provider_key,display_name,enabled,config,created_at,updated_at FROM provider_configs ORDER BY provider_key LIMIT %s OFFSET %s"),"knowledge":("admin.knowledge.read","SELECT id,user_id,kind,left(content,1000) AS content,metadata,created_at FROM memories ORDER BY created_at DESC LIMIT %s OFFSET %s"),"learning-requests":("admin.learning.read","SELECT id,actor_user_id,action,resource_id,outcome,created_at,details FROM audit_logs WHERE action LIKE 'learning.%' ORDER BY created_at DESC LIMIT %s OFFSET %s"),"reports":("admin.reports.read","SELECT id,actor_user_id,action,resource_id,outcome,created_at,details FROM audit_logs ORDER BY created_at DESC LIMIT %s OFFSET %s"),"rules":("admin.rules.read","SELECT action,roles,approval_required,restricted,updated_at FROM admin_rules ORDER BY action LIMIT %s OFFSET %s"),"audit-logs":("admin.audit.read","SELECT id,actor_user_id,action,resource_id,outcome,created_at,details FROM audit_logs ORDER BY created_at DESC LIMIT %s OFFSET %s")}
        if kind not in specs:raise AdminError("unknown administrative resource")
        action,sql=specs[kind];self._authorize(context,action);params=(limit,offset)
        if kind=="users" and query:sql="SELECT id,email,display_name,status,created_at FROM users WHERE email ILIKE %s OR display_name ILIKE %s ORDER BY created_at DESC LIMIT %s OFFSET %s";params=(f"%{query[:100]}%",f"%{query[:100]}%",limit,offset)
        return self._query(sql,params,context.user_id)
    def update_user(self,context:AuthContext,user_id:str,*,status:str|None=None,roles:list[str]|None=None)->dict[str,Any]:
        self._authorize(context,"admin.users.manage",user_id)
        if status is None and roles is None:raise AdminError("at least one user change is required")
        if status is not None and status not in {"active","disabled","pending"}:raise AdminError("invalid user status")
        if roles is not None and (not roles or len(roles)>20 or len(set(roles))!=len(roles)):raise AdminError("invalid roles")
        with self.database.connection(context.user_id) as conn:
            row=None
            if status is not None:row=conn.execute("UPDATE users SET status=%s,updated_at=now() WHERE id=%s RETURNING id,email,display_name,status,created_at",(status,user_id)).fetchone()
            if row is None:row=conn.execute("SELECT id,email,display_name,status,created_at FROM users WHERE id=%s",(user_id,)).fetchone()
            if row is None:raise AdminError("user not found")
            if roles is not None:
                found=conn.execute("SELECT name FROM roles WHERE name=ANY(%s)",(roles,)).fetchall()
                if {r[0] if not isinstance(r,dict) else r["name"] for r in found}!=set(roles):raise AdminError("unknown role")
                conn.execute("DELETE FROM user_roles WHERE user_id=%s",(user_id,));conn.execute("INSERT INTO user_roles(user_id,role_id) SELECT %s,id FROM roles WHERE name=ANY(%s)",(user_id,roles))
            public=dict(row) if isinstance(row,dict) else dict(zip(("id","email","display_name","status","created_at"),row))
        self.audit.record(action="admin.user.updated",actor_user_id=context.user_id,resource_type="user",resource_id=user_id,details={"status_changed":status is not None,"roles_changed":roles is not None});return public
    def create_rule(self,context:AuthContext,action:str,roles:list[str],approval_required:bool=False,restricted:bool=False)->dict[str,Any]:
        self._authorize(context,"admin.rules.manage",action)
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{0,126}",action) or not roles or len(roles)>20 or len(set(roles))!=len(roles):raise AdminError("invalid rule")
        if restricted and not approval_required:raise AdminError("restricted rules require approval")
        found=self._query("SELECT name FROM roles WHERE name=ANY(%s)",(roles,),context.user_id)
        if {r["name"] for r in found}!=set(roles):raise AdminError("unknown role")
        current=self.policies.get(action)
        if current is not None:
            if current.roles==frozenset(roles) and current.approval_required==approval_required and current.restricted==restricted:return {"action":action,"roles":roles,"approval_required":approval_required,"restricted":restricted}
            raise AdminError("permission action already exists")
        self._query("INSERT INTO admin_rules(action,roles,approval_required,restricted,updated_by) VALUES (%s,%s,%s,%s,%s)",(action,roles,approval_required,restricted,context.user_id),context.user_id,fetch=False)
        self.policies.register(Policy(action,frozenset(roles),approval_required,restricted));self.audit.record(action="admin.rule.created",actor_user_id=context.user_id,resource_type="rule",resource_id=action)
        return {"action":action,"roles":roles,"approval_required":approval_required,"restricted":restricted}
    def service_control(self,context:AuthContext,service:str,enabled:bool)->dict[str,Any]:
        self._authorize(context,"admin.services.control",service)
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}",service) or not isinstance(enabled,bool):raise AdminError("invalid service control request")
        self._query("INSERT INTO service_controls(service,enabled,updated_by,updated_at) VALUES (%s,%s,%s,now()) ON CONFLICT(service) DO UPDATE SET enabled=EXCLUDED.enabled,updated_by=EXCLUDED.updated_by,updated_at=now()",(service,enabled,context.user_id),context.user_id,fetch=False)
        self.audit.record(action="admin.service.controlled",actor_user_id=context.user_id,resource_type="service",resource_id=service,details={"enabled":enabled});return {"service":service,"enabled":enabled}
    def analytics(self,context:AuthContext)->dict[str,Any]:
        self._authorize(context,"admin.analytics.read");users=self._query("SELECT status,count(*)::bigint AS count FROM users GROUP BY status",caller=context.user_id);models=self._query("SELECT count(*)::bigint AS count FROM provider_configs WHERE enabled",caller=context.user_id)
        return {"users_by_status":users,"enabled_model_providers":models[0]["count"] if models else 0}
    def emergency(self,context:AuthContext,engage:bool,reason:str="")->dict[str,Any]:
        action="admin.emergency.engage" if engage else "admin.emergency.reset";self._authorize(context,action,"global")
        if engage:
            if not reason.strip() or len(reason)>256:raise AdminError("a bounded emergency reason is required")
            self.actions._stop.engage(context.user_id,reason)
        else:self.actions._stop.reset(context.user_id)
        return {"stopped":self.actions._stop.stopped}
    def audit_events(self,context:AuthContext,limit:int=100)->list[dict[str,Any]]:
        if isinstance(limit,bool) or not 1<=limit<=100:raise AdminError("invalid limit")
        self._authorize(context,"admin.audit.read");return self._query("SELECT id,actor_user_id,action,resource_id,created_at,details FROM audit_logs ORDER BY created_at DESC LIMIT %s",(limit,),context.user_id)
__all__=["AdminError","AdminService"]
