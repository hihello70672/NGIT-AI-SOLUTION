"""Billing domain logic with provider-independent payment verification.

The in-memory repository is intentionally suitable for tests and single-process
local development only. Production persistence requires a reviewed database adapter.
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

from services.api.security import AuthContext, AuditLogger, PolicyEngine


class BillingError(ValueError):
    """Expected billing rejection with a safe user-facing message."""


@dataclass(frozen=True)
class PaymentVerification:
    verified: bool
    provider_reference: str
    status: str
    amount_minor: int
    currency: str


class PaymentProvider(Protocol):
    """Provider adapter boundary; implementations verify facts, never trust clients."""
    def verify_payment(self, reference: str, expected_amount_minor: int, currency: str) -> PaymentVerification: ...
    def verify_webhook(self, raw_body: bytes, signature: str) -> Mapping[str, Any]: ...


class InMemoryPaymentProvider:
    """Deterministic test adapter, not a real payment integration."""
    def __init__(self, webhook_secret: bytes = b"test-only-secret") -> None:
        self._webhook_secret = webhook_secret
        self._payments: dict[str, PaymentVerification] = {}

    def add_payment(self, reference: str, amount_minor: int, currency: str, status: str = "succeeded") -> None:
        self._payments[reference] = PaymentVerification(status == "succeeded", reference, status, amount_minor, currency)

    def verify_payment(self, reference: str, expected_amount_minor: int, currency: str) -> PaymentVerification:
        item = self._payments.get(reference)
        if item is None:
            return PaymentVerification(False, reference, "not_found", 0, currency)
        exact = item.amount_minor == expected_amount_minor and item.currency == currency
        return PaymentVerification(item.verified and exact, item.provider_reference, item.status if exact else "amount_mismatch", item.amount_minor, item.currency)

    def sign_webhook(self, raw_body: bytes) -> str:
        return hmac.new(self._webhook_secret, raw_body, hashlib.sha256).hexdigest()

    def verify_webhook(self, raw_body: bytes, signature: str) -> Mapping[str, Any]:
        expected = self.sign_webhook(raw_body)
        if not hmac.compare_digest(expected, signature):
            raise BillingError("Invalid webhook signature")
        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError) as exc:
            raise BillingError("Invalid webhook payload") from exc
        if not isinstance(payload, dict):
            raise BillingError("Invalid webhook payload")
        return payload


class BillingService:
    """Plans, subscriptions, metering and payment lifecycle operations."""
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
            raise BillingError("Authenticated caller required")
        return context.user_id

    def add_plan(self, plan_key: str, name: str, currency: str, amount_minor: int, interval: str, entitlements: Mapping[str, int]) -> dict[str, Any]:
        if not plan_key or len(plan_key) > 64 or not name or len(name) > 128 or not currency.isalpha() or len(currency) != 3 or amount_minor < 0 or interval not in {"month", "year", "once"}:
            raise BillingError("Invalid plan")
        limits = dict(entitlements)
        if any(not isinstance(k, str) or not k or isinstance(v, bool) or not isinstance(v, int) or v < 0 for k, v in limits.items()):
            raise BillingError("Invalid plan entitlements")
        with self._lock:
            if plan_key in self._plans:
                raise BillingError("Plan already exists")
            plan = {"id": str(uuid.uuid4()), "plan_key": plan_key, "name": name, "currency": currency.upper(), "amount_minor": amount_minor, "billing_interval": interval, "entitlements": limits, "active": True}
            self._plans[plan_key] = plan
            return dict(plan)

    def list_plans(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(plan) for plan in self._plans.values() if plan["active"]]

    def subscribe(self, context: AuthContext, plan_key: str, payment_reference: str) -> dict[str, Any]:
        owner = self._owner(context)
        with self._lock:
            plan = self._plans.get(plan_key)
            if not plan or not plan["active"]:
                raise BillingError("Plan is unavailable")
            verified = self.provider.verify_payment(payment_reference, plan["amount_minor"], plan["currency"])
            if not verified.verified or verified.status != "succeeded":
                raise BillingError("Payment could not be verified")
            now = self.clock()
            end = now + (timedelta(days=365) if plan["billing_interval"] == "year" else timedelta(days=30)) if plan["billing_interval"] != "once" else None
            sub = {"id": str(uuid.uuid4()), "user_id": owner, "plan_key": plan_key, "status": "active", "current_period_start": now.isoformat(), "current_period_end": end.isoformat() if end else None, "cancel_at_period_end": False, "provider_reference": verified.provider_reference}
            self._subscriptions[sub["id"]] = sub
            self._payments.append({"id": str(uuid.uuid4()), "user_id": owner, "subscription_id": sub["id"], "provider_reference": verified.provider_reference, "amount_minor": verified.amount_minor, "currency": verified.currency, "status": "succeeded", "created_at": now.isoformat(), "refund_reference": None})
            self.audit.record(action="billing.subscription.created", actor_user_id=owner, resource_type="subscription", resource_id=sub["id"], details={"plan_key": plan_key})
            return dict(sub)

    def subscription(self, context: AuthContext) -> dict[str, Any] | None:
        owner = self._owner(context)
        with self._lock:
            rows = [s for s in self._subscriptions.values() if s["user_id"] == owner and s["status"] in {"active", "past_due"}]
            return dict(max(rows, key=lambda x: x["current_period_start"])) if rows else None

    def record_usage(self, context: AuthContext, metric: str, quantity: int, *, idempotency_key: str) -> dict[str, Any]:
        owner = self._owner(context)
        if not metric or len(metric) > 100 or isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0 or not idempotency_key or len(idempotency_key) > 128:
            raise BillingError("Invalid usage record")
        with self._lock:
            if any(r["user_id"] == owner and r["idempotency_key"] == idempotency_key for r in self._usage):
                raise BillingError("Usage record already exists")
            sub = self.subscription(context)
            if not sub or sub["status"] != "active":
                raise BillingError("An active subscription is required")
            plan = self._plans[sub["plan_key"]]
            limit = plan["entitlements"].get(metric)
            start = datetime.fromisoformat(sub["current_period_start"])
            used = sum(r["quantity"] for r in self._usage if r["user_id"] == owner and r["metric"] == metric and datetime.fromisoformat(r["recorded_at"]) >= start)
            if limit is not None and used + quantity > limit:
                raise BillingError("Usage quota exceeded")
            row = {"id": str(uuid.uuid4()), "user_id": owner, "subscription_id": sub["id"], "metric": metric, "quantity": quantity, "idempotency_key": idempotency_key, "recorded_at": self.clock().isoformat()}
            self._usage.append(row)
            return dict(row)

    def usage_summary(self, context: AuthContext) -> dict[str, Any]:
        owner = self._owner(context)
        with self._lock:
            sub = self.subscription(context)
            if not sub:
                return {"subscription": None, "usage": {}}
            plan = self._plans[sub["plan_key"]]
            start = datetime.fromisoformat(sub["current_period_start"])
            totals: dict[str, int] = {}
            for row in self._usage:
                if row["user_id"] == owner and datetime.fromisoformat(row["recorded_at"]) >= start:
                    totals[row["metric"]] = totals.get(row["metric"], 0) + row["quantity"]
            return {"subscription": sub, "usage": {key: {"used": totals.get(key, 0), "limit": value} for key, value in plan["entitlements"].items()}}

    def payment_history(self, context: AuthContext) -> list[dict[str, Any]]:
        owner = self._owner(context)
        with self._lock:
            return [dict(item) for item in self._payments if item["user_id"] == owner]

    def cancel_renewal(self, context: AuthContext) -> dict[str, Any]:
        owner = self._owner(context)
        with self._lock:
            sub = self.subscription(context)
            if not sub:
                raise BillingError("No active subscription")
            target = self._subscriptions[sub["id"]]
            target["cancel_at_period_end"] = True
            self.audit.record(action="billing.renewal.cancelled", actor_user_id=owner, resource_type="subscription", resource_id=target["id"])
            return dict(target)

    def renew(self, subscription_id: str, payment_reference: str) -> dict[str, Any]:
        with self._lock:
            sub = self._subscriptions.get(subscription_id)
            if not sub or sub["status"] != "active" or sub["cancel_at_period_end"]:
                raise BillingError("Subscription is not renewable")
            plan = self._plans[sub["plan_key"]]
            verified = self.provider.verify_payment(payment_reference, plan["amount_minor"], plan["currency"])
            if not verified.verified or verified.status != "succeeded":
                sub["status"] = "past_due"
                raise BillingError("Renewal payment could not be verified")
            now = self.clock()
            old_end = datetime.fromisoformat(sub["current_period_end"]) if sub["current_period_end"] else now
            base = max(old_end, now)
            end = base + (timedelta(days=365) if plan["billing_interval"] == "year" else timedelta(days=30))
            sub.update(current_period_start=now.isoformat(), current_period_end=end.isoformat(), provider_reference=verified.provider_reference)
            self._payments.append({"id": str(uuid.uuid4()), "user_id": sub["user_id"], "subscription_id": sub["id"], "provider_reference": verified.provider_reference, "amount_minor": verified.amount_minor, "currency": verified.currency, "status": "succeeded", "created_at": now.isoformat(), "refund_reference": None})
            return dict(sub)

    def refund(self, context: AuthContext, payment_id: str, refund_reference: str) -> dict[str, Any]:
        owner = self._owner(context)
        self.policies.authorize(context, "billing.refund", owner_id=owner)
        if not refund_reference or len(refund_reference) > 256:
            raise BillingError("Invalid refund reference")
        with self._lock:
            payment = next((p for p in self._payments if p["id"] == payment_id and p["user_id"] == owner), None)
            if payment is None:
                raise BillingError("Payment not found")
            if payment["status"] == "refunded":
                return dict(payment)
            payment.update(status="refunded", refund_reference=refund_reference)
            sub = self._subscriptions.get(payment["subscription_id"])
            if sub and sub["status"] == "active":
                sub["status"] = "cancelled"
            self.audit.record(action="billing.payment.refunded", actor_user_id=owner, resource_type="payment", resource_id=payment_id)
            return dict(payment)

    def process_webhook(self, raw_body: bytes, signature: str) -> dict[str, Any]:
        event = self.provider.verify_webhook(raw_body, signature)
        event_id, event_type = event.get("id"), event.get("type")
        if not isinstance(event_id, str) or not event_id or not isinstance(event_type, str):
            raise BillingError("Invalid webhook event")
        with self._lock:
            if event_id in self._webhooks:
                return {"accepted": True, "duplicate": True}
            result = {"accepted": True, "duplicate": False, "event_id": event_id, "type": event_type}
            self._webhooks[event_id] = result
            if event_type == "payment.refunded":
                reference = event.get("payment_reference")
                payment = next((p for p in self._payments if p["provider_reference"] == reference), None)
                if payment:
                    payment["status"] = "refunded"
                    payment["refund_reference"] = str(event.get("refund_reference", ""))[:256]
                    sub = self._subscriptions.get(payment["subscription_id"])
                    if sub:
                        sub["status"] = "cancelled"
            return dict(result)
PY
