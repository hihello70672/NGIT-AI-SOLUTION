-- Billing lifecycle schema. Payment provider remains an injected adapter; no provider credentials are stored.
CREATE TABLE IF NOT EXISTS ngit.billing_payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES ngit.users(id) ON DELETE CASCADE,
    subscription_id uuid NOT NULL REFERENCES ngit.subscriptions(id) ON DELETE CASCADE,
    provider_reference text NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    status text NOT NULL CHECK (status IN ('succeeded','failed','refunded')),
    refund_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(provider_reference)
);
CREATE TABLE IF NOT EXISTS ngit.billing_webhook_events (
    event_id text PRIMARY KEY,
    event_type text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    outcome text NOT NULL DEFAULT 'received'
);
ALTER TABLE ngit.billing_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.billing_payments FORCE ROW LEVEL SECURITY;
CREATE POLICY billing_payments_owner_select ON ngit.billing_payments FOR SELECT USING (user_id = nullif(current_setting('ngit.user_id', true), '')::uuid);
CREATE POLICY billing_payments_owner_insert ON ngit.billing_payments FOR INSERT WITH CHECK (user_id = nullif(current_setting('ngit.user_id', true), '')::uuid);
ALTER TABLE ngit.billing_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.billing_webhook_events FORCE ROW LEVEL SECURITY;
CREATE POLICY billing_webhook_events_no_user_access ON ngit.billing_webhook_events FOR ALL USING (false) WITH CHECK (false);
