# Billing interface

## Ownership and security

Billing derives identity from server-authenticated `AuthContext`; request data cannot specify owner, roles, permissions or approval. Subscription, metering and payment history are owner-scoped. Refund checks the shared `PolicyEngine` and fails closed. Webhooks deliberately do not use bearer auth, but require provider-adapter signature verification, a validated event envelope and provider-key routing. Event IDs are replay-deduplicated. Never put provider keys, credentials, card data or webhook secrets in billing persistence or responses.

## Provider contract

`PaymentProvider.verify_payment(reference, expected_amount_minor, currency)` returns typed `PaymentVerification`; subscription and renewal state changes occur only when verification succeeds with exact amount and currency. `verify_webhook(raw_body, signature)` verifies authenticity and returns parsed event data. Provider-specific libraries, checkout, network calls and credentials remain outside this module. `InMemoryPaymentProvider` is a deterministic test adapter and is not a payment integration.

## Service and routes

Plans use integer minor units, three-letter currency, month/year/once intervals and nonnegative integer entitlements. Purchases create subscription/history only after verification. Metered events require positive quantity and idempotency key; quota is checked under the service lock. Cancellation stops renewal but preserves period access. Renewal records a verified payment or marks past due. Refund workflow updates history and subscription status. Routes mounted under `/api/v1/billing`: `GET /plans`, `GET /subscription`, `POST /subscriptions`, `GET|POST /usage`, `GET /payments`, `POST /renewal/cancel`, `POST /refunds`, and `POST /webhooks/{provider_key}`.

## Persistence and operations

The service is currently in-memory and single-process; migration `0007_billing_lifecycle.sql` is only a database schema/RLS contract, not an integrated persistence adapter. Production requires reviewed transactional persistence for plans, subscriptions, usage, payments and webhook idempotency; non-owner/non-superuser RLS/grant validation; a real provider adapter; verified provider-specific webhook routing; refund execution/verification; renewal scheduler and reconciliation before enabling real transactions. No payment provider is selected here.
