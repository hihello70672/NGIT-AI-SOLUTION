# Billing module

Billing owns plan definitions, owner-scoped subscriptions, usage records and quotas, payment history, renewal state, refunds, and webhook event deduplication. `PaymentProvider` is the adapter boundary for independent verification of payment amount/currency/status and authentic webhook payloads. No concrete commercial payment integration is selected or configured.

The shipped `InMemoryPaymentProvider` and service repository are deterministic local/test implementations only. They are process-local, not durable or safe for multi-worker production; a production deployment must provide reviewed database-backed billing persistence and a provider adapter with authenticated verification before enabling payment operations. Never accept client claims of payment success. Webhook provider signatures must be verified by the injected adapter. Refund route is admin-only through server-side policy registration; caller identity is never read from request data.

Routes under `/api/v1/billing`: plans (GET), subscription (GET), subscriptions (POST), usage (GET/POST), payments (GET), renewal/cancel (POST), refunds (POST), and webhooks/{provider_key} (POST). Webhook event ID deduplication currently shares the process-local repository. The migration provides the durable table/RLS contract but is not wired as a persistence adapter.
