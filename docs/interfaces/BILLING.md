# Billing interface

## Ownership and security

Billing consumes `AuthContext` produced by the API authentication dependency. User IDs, roles and permissions are never accepted from request bodies. Subscription, usage, payment-history and refund lookup are owner-scoped. Refund permission is checked by the shared `PolicyEngine`; a denied or unknown action fails closed. The webhook endpoint is unauthenticated at the bearer layer by design, but processing requires provider-adapter signature verification and event-ID idempotency. Provider keys, credentials, card data and webhook secrets are not stored in billing records.

## Provider contract

`PaymentProvider.verify_payment(reference, expected_amount_minor, currency)` returns a typed `PaymentVerification`; subscriptions and renewals are created only when verified status and expected amount/currency match. `verify_webhook(raw_body, signature)` validates authenticity and returns a parsed event mapping. Provider-specific SDKs, checkout flows, credentials and network calls remain outside the billing module and are not selected here.

## Service behavior

Plans use integer minor currency units, three-letter currency codes, month/year/once intervals, and nonnegative integer entitlement limits. Subscription purchase creates the subscription and payment history only after independent verification. Usage events require a caller-provided idempotency key, positive quantity and active subscription; quota overflow is rejected atomically. Usage summaries are scoped to the current subscription period. Cancellation disables future renewal but keeps the current subscription active through the period. Renewal records verified payment or marks the subscription past due. Refunds update history and cancel the subscription; webhook event IDs are deduplicated.

## Routes and persistence caveats

Routes are mounted below `/api/v1/billing` and documented in `services/api/modules/billing/README.md`. The included service and test payment adapter use process-local state solely to support deterministic unit tests/local development. They do not constitute durable production billing or an actual payment integration. Migration `0007_billing_lifecycle.sql` declares owner-protected payment rows and inaccessible webhook-event storage, but no database persistence adapter is wired. Production must add and validate a transactional DB adapter, database grants/RLS, replay protection, refund-provider execution/verification, and operational renewal scheduling before activation.
