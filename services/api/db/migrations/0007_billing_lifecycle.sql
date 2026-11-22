-- Billing lifecycle schema; provider credentials and payment secrets are never persisted here.
CREATE TABLE IF NOT EXISTS ngit.billing_payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES ngit.users(id) ON DELETE CASCADE,
    subscription_id uuid NOT NULL REFERENCES ngit.subscriptions(id) ON DELETE CASCADE,
    provider_key text NOT NULL CHECK (length(provider_key) BETWEEN 1 AND 64),
    provider_reference text NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    status text NOT NULL CHECK (status IN ('succeeded','failed','refunded')),
    refund_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(provider_key, provider_reference)
);
CREATE TABLE IF NOT EXISTS ngit.billing_webhook_events (
    provider_key text NOT NULL CHECK (length(provider_key) BETWEEN 1 AND 64),
    event_id text NOT NULL,
    event_type text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    outcome text NOT NULL DEFAULT 'received',
    PRIMARY KEY(provider_key, event_id)
);
ALTER TABLE ngit.billing_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.billing_payments FORCE ROW LEVEL SECURITY;
CREATE POLICY billing_payments_owner_select ON ngit.billing_payments FOR SELECT USING (user_id = nullif(current_setting('ngit.user_id', true), '')::uuid);
CREATE POLICY billing_payments_owner_insert ON ngit.billing_payments FOR INSERT WITH CHECK (user_id = nullif(current_setting('ngit.user_id', true), '')::uuid);
ALTER TABLE ngit.billing_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.billing_webhook_events FORCE ROW LEVEL SECURITY;
CREATE POLICY billing_webhook_events_no_user_access ON ngit.billing_webhook_events FOR ALL USING (false) WITH CHECK (false);
