# Billing interface

## Ownership and security

Billing derives identity from authenticated server-side caller context. Request payloads cannot select owner, roles, permissions or approval. Plans, subscription, metering and payment history are owner-scoped. Refund and restricted operations use shared policy and fail closed. Webhooks require provider-adapter signature verification, a validated event envelope, provider-key routing and replay deduplication. Never persist provider secrets, credentials or card data in billing records/responses.

## Provider contract

`PaymentProvider.verify_payment(reference, expected_amount_minor, currency)` returns typed verification. Subscription/history state changes only after successful verification of exact amount/currency. `verify_webhook(raw_body, signature)` authenticates and parses provider events. Provider-specific libraries/network credentials remain behind the adapter. An in-memory test provider is deterministic test-only and is not a real payment integration.

## Service behavior

Plans use integer minor currency units, three-letter currency, supported intervals and nonnegative entitlements. Purchases create subscription/history only after verification. Metering requires positive quantity and idempotency; quota checks are transactionally serialized. Cancellation prevents renewal while preserving paid-period access. Renewal must record a verified payment or mark the period past due. Refund updates history/subscription only according to verified execution.

Existing routes are under `/api/v1/billing`: `GET /plans`, `GET /subscription`, `POST /subscriptions`, `GET|POST /usage`, `GET /payments`, `POST /renewal/cancel`, `POST /refunds`, and provider-key routed `POST /webhooks/{provider_key}`. Preserve implementation compatibility when extending.

## Persistence and operational limits

Status documents current billing/provider execution as in-memory and single-process; migration `0007_billing_lifecycle.sql` is a schema/RLS contract, not an integrated DB adapter. Production requires transactional durable plans/subscriptions/usage/payments/webhook idempotency, a real selected provider, provider-specific webhook verification/routing, refund execution/verification, renewal scheduling and reconciliation, and non-owner/non-superuser grants/RLS validation. No provider is selected here. Do not claim production billing until those requirements are implemented and tested.
