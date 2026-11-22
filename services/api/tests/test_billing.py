"""Billing lifecycle, provider boundary, quota and HTTP tests."""
import json
from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import AuthContext, AuditLogger, PolicyEngine, Policy
from services.api.modules.billing.service import BillingError, BillingService, InMemoryPaymentProvider
from services.api.modules.billing.api import create_billing_router


def setup_service():
    provider = InMemoryPaymentProvider(b"unit-test-webhook-key")
    policies = PolicyEngine()
    policies.register(Policy("billing.refund", frozenset({"admin"})))
    audit = AuditLogger()
    service = BillingService(provider, policies, audit)
    plan = service.add_plan("starter", "Starter", "USD", 500, "month", {"requests": 3})
    provider.add_payment("pay-1", 500, "USD")
    return service, provider, audit, plan


def test_plan_payment_subscription_and_owner_scoped_history():
    service, _, _, _ = setup_service()
    owner = AuthContext("owner", frozenset({"user"}))
    other = AuthContext("other", frozenset({"user"}))
    sub = service.subscribe(owner, "starter", "pay-1")
    assert sub["status"] == "active"
    assert service.subscription(owner)["id"] == sub["id"]
    assert len(service.payment_history(owner)) == 1
    assert service.payment_history(other) == []
    with pytest.raises(BillingError):
        service.subscribe(other, "starter", "missing")


def test_usage_quota_and_idempotency():
    service, provider, _, _ = setup_service()
    provider.add_payment("pay-2", 500, "USD")
    owner = AuthContext("owner", frozenset({"user"}))
    service.subscribe(owner, "starter", "pay-1")
    service.record_usage(owner, "requests", 2, idempotency_key="event-1")
    with pytest.raises(BillingError, match="already exists"):
        service.record_usage(owner, "requests", 1, idempotency_key="event-1")
    with pytest.raises(BillingError, match="quota"):
        service.record_usage(owner, "requests", 2, idempotency_key="event-2")
    assert service.usage_summary(owner)["usage"]["requests"] == {"used": 2, "limit": 3}


def test_renewal_cancel_refund_and_webhook_deduplication():
    service, provider, _, _ = setup_service()
    owner = AuthContext("admin-user", frozenset({"admin"}))
    sub = service.subscribe(owner, "starter", "pay-1")
    provider.add_payment("pay-3", 500, "USD")
    renewed = service.renew(sub["id"], "pay-3")
    assert renewed["id"] == sub["id"]
    payment = service.payment_history(owner)[0]
    refunded = service.refund(owner, payment["id"], "refund-1")
    assert refunded["status"] == "refunded"
    body = json.dumps({"id": "evt-1", "type": "payment.refunded", "payment_reference": "pay-3", "refund_reference": "refund-3"}).encode()
    signature = provider.sign_webhook(body)
    assert service.process_webhook(body, signature)["duplicate"] is False
    assert service.process_webhook(body, signature)["duplicate"] is True
    with pytest.raises(BillingError, match="signature"):
        service.process_webhook(body, "bad")


def test_cancellation_is_at_period_end_and_prevents_renewal():
    service, provider, _, _ = setup_service()
    owner = AuthContext("owner", frozenset({"user"}))
    sub = service.subscribe(owner, "starter", "pay-1")
    assert service.cancel_renewal(owner)["cancel_at_period_end"] is True
    provider.add_payment("pay-next", 500, "USD")
    with pytest.raises(BillingError, match="not renewable"):
        service.renew(sub["id"], "pay-next")


def test_billing_http_routes_derive_owner_from_auth_context():
    service, _, _, _ = setup_service()
    app = FastAPI()
    app.include_router(create_billing_router(service, lambda: AuthContext("owner", frozenset({"user"}))), prefix="/api/v1")
    client = TestClient(app)
    assert client.get("/api/v1/billing/plans").status_code == 200
    assert client.get("/api/v1/billing/payments").json() == {"payments": []}
    response = client.post("/api/v1/billing/subscriptions", json={"plan_key": "starter", "payment_reference": "pay-1"})
    assert response.status_code == 201
    assert response.json()["subscription"]["user_id"] == "owner"
