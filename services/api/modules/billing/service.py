"""Provider-agnostic billing domain logic.

In-memory state and adapter are intended for deterministic tests/local development;
production must inject durable transactional storage and a real verification adapter.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Protocol
from services.api.security import AuthContext, AuditLogger, PolicyEngine, SecurityError

class BillingError(ValueError):
    """Expected billing rejection with a safe message."""

@dataclass(frozen=True)
class PaymentVerification:
    verified: bool
    provider_reference: str
    status: str
    amount_minor: int
    currency: str

class PaymentProvider(Protocol):
    def verify_payment(self, reference: str, expected_amount_minor: int, currency: str) -> PaymentVerification: ...
    def verify_webhook(self, raw_body: bytes, signature: str) -> Mapping[str, Any]: ...

class InMemoryPaymentProvider:
    """Test-only adapter. It does not communicate with a payment provider."""
    def __init__(self, webhook_secret: bytes = b"test-only-secret") -> None:
        self._webhook_secret = webhook_secret
        self._payments: dict[str, PaymentVerification] = {}
    def add_payment(self, reference: str, amount_minor: int, currency: str, status: str = "succeeded") -> None:
        self._payments[reference] = PaymentVerification(status == "succeeded", reference, status, amount_minor, currency.upper())
    def verify_payment(self, reference: str, expected_amount_minor: int, currency: str) -> PaymentVerification:
        item = self._payments.get(reference)
        if item is None:
            return PaymentVerification(False, reference, "not_found", 0, currency.upper())
        exact = item.amount_minor == expected_amount_minor and item.currency == currency.upper()
        return PaymentVerification(item.verified and exact, item.provider_reference, item.status if exact else "amount_mismatch", item.amount_minor, item.currency)
    def sign_webhook(self, raw_body: bytes) -> str:
        return hmac.new(self._webhook_secret, raw_body, hashlib.sha256).hexdigest()
    def verify_webhook(self, raw_body: bytes, signature: str) -> Mapping[str, Any]:
        if not hmac.compare_digest(self.sign_webhook(raw_body), signature):
            raise BillingError("Invalid webhook signature")
        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError) as exc:
            raise BillingError("Invalid webhook payload") from exc
        if not isinstance(payload, dict):
            raise BillingError("Invalid webhook payload")
        return payload

class BillingService:
    """Plans, owner-scoped subscriptions, metering and lifecycle records."""
    def __init__(self, provider: PaymentProvider, policies: PolicyEngine, audit: AuditLogger, *, clock=lambda: datetime.now(timezone.utc)) -> None:
        self.provider, self.policies, self.audit, self.clock = provider, policies, audit, clock
        self._lock = threading.RLock()
        self._plans: dict[str, dict[str, Any]] = {}
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._usage: list[dict[str, Any]] = []
        self._payments: list[dict[str, Any]] = []
        self._webhooks: dict[str, dict[str, Any]] = {}
    @staticmethod
    def _owner(context: AuthContext) -> str:
        if not isinstance(context, AuthContext) or not context.user_id:
            raise SecurityError("unauthenticated", "Authentication required")
        return context.user_id
    def add_plan(self, plan_key: str, name: str, currency: str, amount_minor: int, interval: str, entitlements: Mapping[str, int]) -> dict[str, Any]:
        if not isinstance(plan_key, str) or not plan_key or len(plan_key)>64 or not isinstance(name,str) or not name or len(name)>128 or not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha() or isinstance(amount_minor,bool) or not isinstance(amount_minor,int) or amount_minor<0 or interval not in {"month","year","once"}:
            raise BillingError("Invalid plan")
        limits=dict(entitlements)
        if any(not isinstance(k,str) or not k or isinstance(v,bool) or not isinstance(v,int) or v<0 for k,v in limits.items()): raise BillingError("Invalid plan entitlements")
        with self._lock:
            if plan_key in self._plans: raise BillingError("Plan already exists")
            plan={"id":str(uuid.uuid4()),"plan_key":plan_key,"name":name,"currency":currency.upper(),"amount_minor":amount_minor,"billing_interval":interval,"entitlements":limits,"active":True}
            self._plans[plan_key]=plan
            return dict(plan)
    def list_plans(self)->list[dict[str,Any]]:
        with self._lock:return [dict(p) for p in self._plans.values() if p["active"]]
    def subscribe(self, context:AuthContext, plan_key:str, payment_reference:str)->dict[str,Any]:
        owner=self._owner(context)
        with self._lock:
            plan=self._plans.get(plan_key)
            if not plan or not plan["active"]:raise BillingError("Plan is unavailable")
            verified=self.provider.verify_payment(payment_reference,plan["amount_minor"],plan["currency"])
            if not verified.verified or verified.status!="succeeded":raise BillingError("Payment could not be verified")
            if any(p["provider_reference"]==verified.provider_reference for p in self._payments):raise BillingError("Payment reference already used")
            now=self.clock();end=now+timedelta(days=365 if plan["billing_interval"]=="year" else 30) if plan["billing_interval"]!="once" else None
            sub={"id":str(uuid.uuid4()),"user_id":owner,"plan_key":plan_key,"status":"active","current_period_start":now.isoformat(),"current_period_end":end.isoformat() if end else None,"cancel_at_period_end":False,"provider_reference":verified.provider_reference}
            self._subscriptions[sub["id"]]=sub
            self._payments.append({"id":str(uuid.uuid4()),"user_id":owner,"subscription_id":sub["id"],"provider_reference":verified.provider_reference,"amount_minor":verified.amount_minor,"currency":verified.currency,"status":"succeeded","created_at":now.isoformat(),"refund_reference":None})
            self.audit.record(action="billing.subscription.created",actor_user_id=owner,resource_type="subscription",resource_id=sub["id"],details={"plan_key":plan_key})
            return dict(sub)
    def subscription(self,context:AuthContext)->dict[str,Any]|None:
        owner=self._owner(context)
        with self._lock:
            rows=[s for s in self._subscriptions.values() if s["user_id"]==owner and s["status"] in {"active","past_due"}]
            return dict(max(rows,key=lambda x:x["current_period_start"])) if rows else None
    def record_usage(self,context:AuthContext,metric:str,quantity:int,*,idempotency_key:str)->dict[str,Any]:
        owner=self._owner(context)
        if not isinstance(metric,str) or not metric or len(metric)>100 or isinstance(quantity,bool) or not isinstance(quantity,int) or quantity<=0 or not isinstance(idempotency_key,str) or not idempotency_key or len(idempotency_key)>128:raise BillingError("Invalid usage record")
        with self._lock:
            if any(r["user_id"]==owner and r["idempotency_key"]==idempotency_key for r in self._usage):raise BillingError("Usage record already exists")
            sub=self.subscription(context)
            if not sub or sub["status"]!="active":raise BillingError("An active subscription is required")
            plan=self._plans[sub["plan_key"]];limit=plan["entitlements"].get(metric);start=datetime.fromisoformat(sub["current_period_start"])
            used=sum(r["quantity"] for r in self._usage if r["user_id"]==owner and r["metric"]==metric and datetime.fromisoformat(r["recorded_at"])>=start)
            if limit is not None and used+quantity>limit:raise BillingError("Usage quota exceeded")
            row={"id":str(uuid.uuid4()),"user_id":owner,"subscription_id":sub["id"],"metric":metric,"quantity":quantity,"idempotency_key":idempotency_key,"recorded_at":self.clock().isoformat()};self._usage.append(row);return dict(row)
    def usage_summary(self,context:AuthContext)->dict[str,Any]:
        owner=self._owner(context)
        with self._lock:
            sub=self.subscription(context)
            if not sub:return {"subscription":None,"usage":{}}
            start=datetime.fromisoformat(sub["current_period_start"]);totals={}
            for row in self._usage:
                if row["user_id"]==owner and row["subscription_id"]==sub["id"] and datetime.fromisoformat(row["recorded_at"])>=start:totals[row["metric"]]=totals.get(row["metric"],0)+row["quantity"]
            return {"subscription":sub,"usage":{k:{"used":totals.get(k,0),"limit":v} for k,v in self._plans[sub["plan_key"]]["entitlements"].items()}}
    def payment_history(self,context:AuthContext)->list[dict[str,Any]]:
        owner=self._owner(context)
        with self._lock:return [dict(p) for p in self._payments if p["user_id"]==owner]
    def cancel_renewal(self,context:AuthContext)->dict[str,Any]:
        owner=self._owner(context)
        with self._lock:
            sub=self.subscription(context)
            if not sub:raise BillingError("No active subscription")
            target=self._subscriptions[sub["id"]];target["cancel_at_period_end"]=True
            self.audit.record(action="billing.renewal.cancelled",actor_user_id=owner,resource_type="subscription",resource_id=target["id"]);return dict(target)
    def renew(self,subscription_id:str,payment_reference:str)->dict[str,Any]:
        with self._lock:
            sub=self._subscriptions.get(subscription_id)
            if not sub or sub["status"]!="active" or sub["cancel_at_period_end"]:raise BillingError("Subscription is not renewable")
            plan=self._plans[sub["plan_key"]];verified=self.provider.verify_payment(payment_reference,plan["amount_minor"],plan["currency"])
            if not verified.verified or verified.status!="succeeded":sub["status"]="past_due";raise BillingError("Renewal payment could not be verified")
            if any(p["provider_reference"]==verified.provider_reference for p in self._payments):raise BillingError("Payment reference already used")
            now=self.clock();old_end=datetime.fromisoformat(sub["current_period_end"]) if sub["current_period_end"] else now;base=max(old_end,now);end=base+timedelta(days=365 if plan["billing_interval"]=="year" else 30)
            sub.update(current_period_start=now.isoformat(),current_period_end=end.isoformat(),provider_reference=verified.provider_reference)
            self._payments.append({"id":str(uuid.uuid4()),"user_id":sub["user_id"],"subscription_id":sub["id"],"provider_reference":verified.provider_reference,"amount_minor":verified.amount_minor,"currency":verified.currency,"status":"succeeded","created_at":now.isoformat(),"refund_reference":None});return dict(sub)
    def refund(self,context:AuthContext,payment_id:str,refund_reference:str)->dict[str,Any]:
        owner=self._owner(context);self.policies.authorize(context,"billing.refund")
        if not isinstance(refund_reference,str) or not refund_reference or len(refund_reference)>256:raise BillingError("Invalid refund reference")
        with self._lock:
            payment=next((p for p in self._payments if p["id"]==payment_id and p["user_id"]==owner),None)
            if payment is None:raise BillingError("Payment not found")
            if payment["status"]=="refunded":return dict(payment)
            payment.update(status="refunded",refund_reference=refund_reference);sub=self._subscriptions.get(payment["subscription_id"])
            if sub and sub["status"]=="active":sub["status"]="cancelled"
            self.audit.record(action="billing.payment.refunded",actor_user_id=owner,resource_type="payment",resource_id=payment_id);return dict(payment)
    def process_webhook(self,raw_body:bytes,signature:str)->dict[str,Any]:
        event=self.provider.verify_webhook(raw_body,signature);event_id,event_type=event.get("id"),event.get("type")
        if not isinstance(event_id,str) or not event_id or len(event_id)>256 or not isinstance(event_type,str) or not event_type:raise BillingError("Invalid webhook event")
        with self._lock:
            if event_id in self._webhooks:return {"accepted":True,"duplicate":True}
            if event_type=="payment.refunded":
                reference=event.get("payment_reference");payment=next((p for p in self._payments if p["provider_reference"]==reference),None)
                if payment:
                    payment["status"]="refunded";payment["refund_reference"]=str(event.get("refund_reference",""))[:256];sub=self._subscriptions.get(payment["subscription_id"])
                    if sub and sub["status"]=="active":sub["status"]="cancelled"
            result={"accepted":True,"duplicate":False,"event_id":event_id,"type":event_type};self._webhooks[event_id]=result;return dict(result)
