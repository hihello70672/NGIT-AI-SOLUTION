"""Authenticated billing HTTP routes."""
from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from services.api.security import AuthContext
from .service import BillingService
class SubscribeRequest(BaseModel):
    plan_key:str=Field(min_length=1,max_length=64)
    payment_reference:str=Field(min_length=1,max_length=256)
class UsageRequest(BaseModel):
    metric:str=Field(min_length=1,max_length=100)
    quantity:int=Field(gt=0)
    idempotency_key:str=Field(min_length=1,max_length=128)
class RefundRequest(BaseModel):
    payment_id:str=Field(min_length=1,max_length=128)
    refund_reference:str=Field(min_length=1,max_length=256)
def create_billing_router(service:BillingService,current_user)->APIRouter:
    router=APIRouter(prefix="/billing",tags=["billing"])
    @router.get("/plans")
    def plans():return {"plans":service.list_plans()}
    @router.get("/subscription")
    def subscription(context:AuthContext=Depends(current_user)):return {"subscription":service.subscription(context)}
    @router.post("/subscriptions",status_code=201)
    def subscribe(body:SubscribeRequest,context:AuthContext=Depends(current_user)):return {"subscription":service.subscribe(context,body.plan_key,body.payment_reference)}
    @router.post("/usage")
    def record_usage(body:UsageRequest,context:AuthContext=Depends(current_user)):return {"usage":service.record_usage(context,body.metric,body.quantity,idempotency_key=body.idempotency_key)}
    @router.get("/usage")
    def usage(context:AuthContext=Depends(current_user)):return service.usage_summary(context)
    @router.get("/payments")
    def payments(context:AuthContext=Depends(current_user)):return {"payments":service.payment_history(context)}
    @router.post("/renewal/cancel")
    def cancel_renewal(context:AuthContext=Depends(current_user)):return {"subscription":service.cancel_renewal(context)}
    @router.post("/refunds")
    def refund(body:RefundRequest,context:AuthContext=Depends(current_user)):return {"payment":service.refund(context,body.payment_id,body.refund_reference)}
    @router.post("/webhooks/{provider_key}")
    async def webhook(provider_key:str,request:Request,signature:str=Header(default="",alias="X-Payment-Signature")):
        if not provider_key or len(provider_key)>64:raise ValueError("Invalid provider key")
        return service.process_webhook(await request.body(),signature)
    return router
__all__=["create_billing_router","SubscribeRequest","UsageRequest","RefundRequest"]
