"""Process-local security primitives for NGIT's modular API.

Tokens, approvals, stop state and audit events are process-local. Multi-worker
or restart-safe deployments require an approved shared persistence adapter.
""" 
from __future__ import annotations

import copy
import hashlib
import hmac
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping


class SecurityError(Exception):
    """Expected security rejection with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


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
    """Environment-backed configuration; secret values are never enumerated."""

    def __init__(self, environ: Mapping[str, str] | None = None):
        self._environ = os.environ if environ is None else environ

    def get(self, name: str) -> str | None:
        if not isinstance(name, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", name):
            raise ValueError("invalid secret name")
        return self._environ.get(name)


class Authenticator:
    """Opaque bearer issue/validation/revocation; stores keyed digests only."""

    def __init__(self, pepper: str | None = None, *, clock: Callable[[], float] = time.time):
        self._pepper = pepper if pepper is not None else SecretStore().get("AUTH_TOKEN_PEPPER")
        if not self._pepper or len(self._pepper.encode()) < 32:
            raise ValueError("AUTH_TOKEN_PEPPER must be configured and at least 32 bytes")
        self._clock, self._lock = clock, threading.RLock()
        self._tokens: dict[str, tuple[AuthContext, float]] = {}

    def _digest(self, token: str) -> str:
        return hmac.new(self._pepper.encode(), token.encode(), hashlib.sha256).hexdigest()

    def issue(self, user_id: str, roles: set[str] | frozenset[str] = frozenset(), *, ttl_seconds: int = 3600) -> str:
        if not isinstance(user_id, str) or not user_id or len(user_id) > 256:
            raise ValueError("invalid token issue parameters")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 86400:
            raise ValueError("invalid token issue parameters")
        if any(not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", role) for role in roles):
            raise ValueError("invalid role")
        token = secrets.token_urlsafe(32)
        context = AuthContext(user_id, frozenset(roles), secrets.token_urlsafe(12))
        with self._lock:
            now = self._clock()
            self._tokens = {key: value for key, value in self._tokens.items() if value[1] > now}
            self._tokens[self._digest(token)] = (context, now + ttl_seconds)
        return token

    def authenticate(self, token: str | None) -> AuthContext:
        if not isinstance(token, str) or not token or len(token) > 512:
            raise SecurityError("unauthenticated", "Authentication required")
        digest = self._digest(token)
        with self._lock:
            item = self._tokens.get(digest)
            if item is None or item[1] <= self._clock():
                self._tokens.pop(digest, None)
                raise SecurityError("unauthenticated", "Authentication required")
            return item[0]

    def revoke(self, token: str) -> None:
        if isinstance(token, str) and len(token) <= 512:
            with self._lock:
                self._tokens.pop(self._digest(token), None)


class AuditLogger:
    """Thread-safe audit sink with recursive sensitive-key/value filtering."""
    _forbidden = {"password", "token", "secret", "credential", "prompt", "authorization", "cookie", "apikey"}

    def __init__(self):
        self._lock = threading.RLock()
        self._events: list[dict[str, Any]] = []

    @classmethod
    def _safe(cls, value: Any, depth: int = 0) -> Any:
        if depth > 8:
            return "[TRUNCATED]"
        if isinstance(value, Mapping):
            result = {}
            for key, item in value.items():
                text = str(key)
                normalized = re.sub(r"[^a-z0-9]", "", text.lower())
                if any(word.replace("_", "") in normalized for word in cls._forbidden):
                    continue
                result[text[:128]] = cls._safe(item, depth + 1)
            return result
        if isinstance(value, (list, tuple)):
            return [cls._safe(item, depth + 1) for item in value[:100]]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            if re.search(r"(?i)\b(bearer\s+\S+|(?:sk|pk|api)[-_][a-z0-9_-]{12,})", value):
                return "[REDACTED]"
            return value[:512]
        return type(value).__name__

    def record(self, *, action: str, actor_user_id: str | None = None,
               resource_type: str | None = None, resource_id: str | None = None,
               request_id: str | None = None, outcome: str = "success",
               details: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(action, str) or not action or len(action) > 128:
            raise ValueError("invalid audit action")
        event = {"action": action, "actor_user_id": self._safe(actor_user_id),
                 "resource_type": self._safe(resource_type), "resource_id": self._safe(resource_id),
                 "request_id": self._safe(request_id), "outcome": self._safe(outcome)[:64],
                 "occurred_at": datetime.now(timezone.utc).isoformat(),
                 "details": self._safe(details or {})}
        with self._lock:
            self._events.append(copy.deepcopy(event))
            return copy.deepcopy(event)

    def events(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(copy.deepcopy(event) for event in self._events)


class PolicyEngine:
    """Explicit default-deny RBAC and resource-owner policy evaluation."""
    def __init__(self, policies: Mapping[str, Policy] | None = None):
        self._policies: dict[str, Policy] = {}
        for action, policy in (policies or {}).items():
            if not isinstance(policy, Policy) or action != policy.action:
                raise ValueError("policy key/action mismatch")
            self._validate(policy)
            self._policies[action] = policy

    @staticmethod
    def _validate(policy: Policy) -> None:
        if not isinstance(policy.action, str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", policy.action):
            raise ValueError("invalid policy action")
        if any(not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", role) for role in policy.roles):
            raise ValueError("invalid policy role")
        if policy.restricted and not policy.approval_required:
            raise ValueError("restricted policies must require approval")

    def register(self, policy: Policy) -> None:
        if not isinstance(policy, Policy):
            raise ValueError("invalid policy")
        self._validate(policy)
        if policy.action in self._policies:
            raise ValueError("policy action must be unique")
        self._policies[policy.action] = policy

    def authorize(self, context: AuthContext, action: str, *, owner_id: str | None = None) -> Policy:
        if not isinstance(context, AuthContext) or not context.user_id:
            raise SecurityError("unauthenticated", "Authentication required")
        policy = self._policies.get(action)
        if policy is None:
            raise SecurityError("forbidden", "Action is not permitted")
        if owner_id is not None and owner_id != context.user_id and "admin" not in context.roles:
            raise SecurityError("forbidden", "Resource access is not permitted")
        if not policy.roles.intersection(context.roles):
            raise SecurityError("forbidden", "Action is not permitted")
        return policy


@dataclass
class Approval:
    approval_id: str
    actor_user_id: str
    action: str
    resource_id: str
    expires_at: float
    status: str = "pending"
    approver_user_id: str | None = None


class ApprovalEngine:
    """One-time expiring grants bound to actor, action and resource."""
    def __init__(self, *, clock: Callable[[], float] = time.time):
        self._clock, self._lock = clock, threading.RLock()
        self._approvals: dict[str, Approval] = {}

    def request(self, actor_user_id: str, action: str, resource_id: str, *, ttl_seconds: int = 600) -> Approval:
        if (not actor_user_id or not action or not resource_id or len(actor_user_id) > 256
                or len(action) > 128 or len(resource_id) > 256 or isinstance(ttl_seconds, bool)
                or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 3600):
            raise ValueError("invalid approval request")
        approval = Approval(secrets.token_urlsafe(18), actor_user_id, action, resource_id, self._clock() + ttl_seconds)
        with self._lock:
            self._approvals[approval.approval_id] = approval
        return copy.deepcopy(approval)

    def decide(self, approval_id: str, approver_user_id: str, *, approved: bool) -> Approval:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None or approval.expires_at <= self._clock() or approval.status != "pending":
                raise SecurityError("approval_invalid", "Approval is missing, expired, or already decided")
            if not approver_user_id or approver_user_id == approval.actor_user_id:
                raise SecurityError("forbidden", "A different approver is required")
            approval.status = "approved" if approved else "rejected"
            approval.approver_user_id = approver_user_id
            return copy.deepcopy(approval)

    def consume(self, approval_id: str, *, actor_user_id: str, action: str, resource_id: str) -> bool:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if (approval is None or approval.status != "approved" or approval.expires_at <= self._clock()
                    or approval.actor_user_id != actor_user_id or approval.action != action
                    or approval.resource_id != resource_id):
                return False
            approval.status = "consumed"
            return True


class EmergencyStop:
    """Fail-closed process switch for restricted operations."""
    def __init__(self, audit: AuditLogger):
        self._audit, self._lock, self._stopped = audit, threading.RLock(), False

    @property
    def stopped(self) -> bool:
        with self._lock:
            return self._stopped

    def engage(self, actor_user_id: str, reason: str) -> None:
        if not actor_user_id or not reason or len(reason) > 256:
            raise ValueError("actor and bounded reason are required")
        with self._lock:
            self._stopped = True
        self._audit.record(action="emergency_stop.engaged", actor_user_id=actor_user_id, details={"reason": reason})

    def reset(self, actor_user_id: str) -> None:
        if not actor_user_id:
            raise ValueError("actor is required")
        with self._lock:
            self._stopped = False
        self._audit.record(action="emergency_stop.reset", actor_user_id=actor_user_id)

    def check(self) -> None:
        if self.stopped:
            raise SecurityError("emergency_stop", "Restricted actions are temporarily disabled")


class RestrictedActionManager:
    """Composes RBAC, ownership, stop switch, approval and audit."""
    def __init__(self, policies: PolicyEngine, approvals: ApprovalEngine,
                 stop: EmergencyStop, audit: AuditLogger):
        self._policies, self._approvals, self._stop, self._audit = policies, approvals, stop, audit

    def authorize(self, context: AuthContext, action: str, resource_id: str, *,
                  owner_id: str | None = None, approval_id: str | None = None) -> None:
        try:
            policy = self._policies.authorize(context, action, owner_id=owner_id)
            if policy.restricted:
                self._stop.check()
            if policy.approval_required and (not approval_id or not self._approvals.consume(
                    approval_id, actor_user_id=context.user_id, action=action, resource_id=resource_id)):
                raise SecurityError("approval_required", "A valid approval is required")
        except SecurityError as exc:
            self._audit.record(action=action if isinstance(action, str) else "unknown",
                               actor_user_id=getattr(context, "user_id", None), resource_id=resource_id,
                               outcome="denied", details={"error_code": exc.code})
            raise
        self._audit.record(action=action, actor_user_id=context.user_id, resource_id=resource_id,
                           outcome="authorized")


def create_default_security() -> tuple[Authenticator, PolicyEngine, ApprovalEngine, AuditLogger, EmergencyStop, RestrictedActionManager]:
    audit = AuditLogger()
    policies = PolicyEngine()
    policies.register(Policy("profile.read", frozenset({"user", "admin"})))
    policies.register(Policy("admin.users.manage", frozenset({"admin"}), approval_required=True, restricted=True))
    approvals, stop = ApprovalEngine(), EmergencyStop(audit)
    actions = RestrictedActionManager(policies, approvals, stop, audit)
    return Authenticator(), policies, approvals, audit, stop, actions


def error_payload(error: SecurityError, request_id: str | None = None) -> dict[str, Any]:
    return {"error": {"code": error.code, "message": error.message,
                      "request_id": request_id, "details": {}}}


__all__ = ["Approval", "ApprovalEngine", "AuthContext", "Authenticator", "AuditLogger",
           "EmergencyStop", "Policy", "PolicyEngine", "RestrictedActionManager",
           "SecretStore", "SecurityError", "create_default_security", "error_payload"]
