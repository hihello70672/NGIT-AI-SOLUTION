"""Billing lifecycle, provider boundary, quota and HTTP regression tests."""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.security import AuthContext, AuditLogger, PolicyEngine, Policy, SecurityError
from services.api.modules.billing.service import BillingError, BillingService, InMemoryPaymentProvider
from services.api.modules.billing.api import create_billing_router


def setup_service():
    provider=InMemoryPaymentProvider(b"unit-test-webhook-key")
    policies=PolicyEngine();policies.register(Policy("billing.refund",frozenset({"admin"})))
    audit=AuditLogger();service=BillingService(provider,policies,audit)
    service.add_plan("starter","Starter","USD",500,"month",{"requests":3})
    provider.add_payment("pay-1",500,"USD")
    return service,provider,audit


def test_payment_verification_subscription_and_owner_scoping():
    service,_,_=setup_service();owner=AuthContext("owner",frozenset({"user"}));other=AuthContext("other",frozenset({"user"}))
    sub=service.subscribe(owner,"starter","pay-1")
    assert sub["status"]=="active" and service.subscription(owner)["id"]==sub["id"]
    assert len(service.payment_history(owner))==1 and service.payment_history(other)==[]
    with pytest.raises(BillingError,match="could not be verified"):service.subscribe(other,"starter","unknown")
    with pytest.raises(BillingError,match="already used"):service.subscribe(owner,"starter","pay-1")


def test_metered_usage_quota_and_idempotency():
    service,_,_=setup_service();owner=AuthContext("owner",frozenset({"user"}));service.subscribe(owner,"starter","pay-1")
    service.record_usage(owner,"requests",2,idempotency_key="req-1")
    with pytest.raises(BillingError,match="already exists"):service.record_usage(owner,"requests",1,idempotency_key="req-1")
    with pytest.raises(BillingError,match="quota"):service.record_usage(owner,"requests",2,idempotency_key="req-2")
    assert service.usage_summary(owner)["usage"]["requests"]=={"used":2,"limit":3}
    with pytest.raises(SecurityError):service.payment_history({"user_id":"owner"})


def test_renewal_cancel_refund_and_verified_deduplicated_webhook():
    service,provider,_=setup_service();owner=AuthContext("admin-user",frozenset({"admin"}));sub=service.subscribe(owner,"starter","pay-1")
    provider.add_payment("pay-2",500,"USD");assert service.renew(sub["id"],"pay-2")["id"]==sub["id"]
    payment=service.payment_history(owner)[0];assert service.refund(owner,payment["id"],"refund-1")["status"]=="refunded"
    body=json.dumps({"id":"evt-1","type":"payment.refunded","payment_reference":"pay-2","refund_reference":"refund-2"}).encode();sig=provider.sign_webhook(body)
    assert service.process_webhook(body,sig)["duplicate"] is False
    assert service.process_webhook(body,sig)["duplicate"] is True
    with pytest.raises(BillingError,match="signature"):service.process_webhook(body,"invalid")


def test_cancellation_blocks_renewal_and_regular_users_cannot_refund():
    service,provider,_=setup_service();user=AuthContext("owner",frozenset({"user"}));sub=service.subscribe(user,"starter","pay-1")
    assert service.cancel_renewal(user)["cancel_at_period_end"]
    provider.add_payment("pay-2",500,"USD")
    with pytest.raises(BillingError,match="not renewable"):service.renew(sub["id"],"pay-2")
    # Policy check happens before any refund lookup or mutation.
    with pytest.raises(SecurityError):service.refund(user,"not-owned","refund")


def test_billing_http_routes_use_authenticated_server_context():
    service,_,_=setup_service();app=FastAPI()
    app.include_router(create_billing_router(service,lambda:AuthContext("owner",frozenset({"user"}))),prefix="/api/v1")
    client=TestClient(app)
    assert client.get("/api/v1/billing/plans").status_code==200
    assert client.get("/api/v1/billing/payments").json()=={"payments":[]}
    result=client.post("/api/v1/billing/subscriptions",json={"plan_key":"starter","payment_reference":"pay-1"})
    assert result.status_code==201 and result.json()["subscription"]["user_id"]=="owner"
    assert client.post("/api/v1/billing/subscriptions",json={"plan_key":"starter","payment_reference":"pay-1","user_id":"attacker"}).status_code==201
