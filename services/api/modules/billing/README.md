# Billing module

Billing owns plans, subscriptions, usage metering and quotas, payment history, renewal state, refunds and webhook processing. `PaymentProvider` defines provider-neutral interfaces for independent payment and webhook verification; no commercial payment provider is selected. No provider secret or client-asserted payment status is accepted.

Routes under `/api/v1/billing` expose plans, subscriptions, usage, payment history, renewal cancellation, refunds and provider-keyed webhooks. Identity is taken from authenticated server-side `AuthContext`. Refund is protected by shared admin policy. The injected payment adapter validates amount/currency/status and authenticates webhook signatures. Webhook processing deduplicates event IDs.

**Operational boundary:** billing state and `InMemoryPaymentProvider` are process-local deterministic test/development implementations, not durable or multi-worker safe. Migration `0007_billing_lifecycle.sql` is a schema contract; database transactions/RLS are not wired into service persistence. Do not enable real payments until durable persistence, provider implementation, production secret management, verified webhook mapping, refund execution, renewal scheduling, and database grants/RLS have been designed and validated.
