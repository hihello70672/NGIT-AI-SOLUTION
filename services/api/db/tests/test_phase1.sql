-- Phase 1 regression tests on a disposable database as a non-owner app role.
BEGIN;
DO $tests$
DECLARE
  u1 uuid;
  u2 uuid;
  c1 uuid;
  rejected boolean := false;
  table_name text;
  required_tables text[] := ARRAY[
    'users','roles','user_roles','conversations','messages','memories',
    'billing_plans','billing_accounts','subscriptions','usage_records',
    'billing_payments','billing_webhook_events','provider_configs',
    'media_assets','videos','presentations','presentation_slides','audit_logs'
  ];
BEGIN
  FOREACH table_name IN ARRAY required_tables LOOP
    IF to_regclass(format('ngit.%I', table_name)) IS NULL THEN
      RAISE EXCEPTION 'required table ngit.% is missing', table_name;
    END IF;
  END LOOP;

  INSERT INTO ngit.users(email,password_hash,display_name)
  VALUES ('phase1-a-' || gen_random_uuid() || '@example.invalid','test-only','Phase 1 A') RETURNING id INTO u1;
  INSERT INTO ngit.users(email,password_hash,display_name)
  VALUES ('phase1-b-' || gen_random_uuid() || '@example.invalid','test-only','Phase 1 B') RETURNING id INTO u2;
  PERFORM set_config('ngit.user_id',u1::text,true);
  INSERT INTO ngit.conversations(user_id,title) VALUES (u1,'tenant A') RETURNING id INTO c1;

  BEGIN
    INSERT INTO ngit.messages(conversation_id,user_id,role,content)
    VALUES (c1,u2,'user','must be rejected');
  EXCEPTION WHEN foreign_key_violation THEN rejected := true;
  END;
  IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant message foreign key was accepted'; END IF;

  IF (SELECT count(*) FROM ngit.conversations WHERE user_id=u2) <> 0 THEN
    RAISE EXCEPTION 'tenant A can read tenant B conversations';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM ngit.roles WHERE name='user') THEN
    RAISE EXCEPTION 'user reference role seed missing';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM ngit.provider_configs WHERE provider_key='local' AND enabled=false) THEN
    RAISE EXCEPTION 'optional local provider seed missing or unexpectedly enabled';
  END IF;
END
$tests$;
ROLLBACK;
