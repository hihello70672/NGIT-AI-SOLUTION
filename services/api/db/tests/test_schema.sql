-- Run with: psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql
BEGIN;
SET search_path TO ngit, public;
DO $test$
DECLARE u1 uuid; u2 uuid; c1 uuid; c2 uuid; rejected boolean := false;
BEGIN
  INSERT INTO users(email,password_hash,display_name) VALUES
    ('db-test-one@example.invalid','not-a-login-hash','Test One'),
    ('db-test-two@example.invalid','not-a-login-hash','Test Two') RETURNING id INTO u1;
  SELECT id INTO u2 FROM users WHERE email='db-test-two@example.invalid';
  INSERT INTO conversations(user_id,title) VALUES(u1,'One') RETURNING id INTO c1;
  INSERT INTO conversations(user_id,title) VALUES(u2,'Two') RETURNING id INTO c2;
  INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'user','hello');
  BEGIN
    INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u2,c1,'user','cross-owner');
  EXCEPTION WHEN foreign_key_violation THEN rejected := true;
  END;
  IF NOT rejected THEN RAISE EXCEPTION 'composite owner FK allowed cross-user message'; END IF;
  PERFORM set_config('ngit.user_id',u1::text,true);
  IF (SELECT count(*) FROM conversations) <> 1 THEN RAISE EXCEPTION 'RLS did not isolate conversations'; END IF;
  IF (SELECT count(*) FROM conversations WHERE id=c2) <> 0 THEN RAISE EXCEPTION 'cross-user conversation visible'; END IF;
  rejected := false;
  BEGIN
    INSERT INTO conversations(user_id,title) VALUES(u2,'RLS write attempt');
  EXCEPTION WHEN insufficient_privilege THEN rejected := true;
  END;
  IF NOT rejected THEN RAISE EXCEPTION 'RLS did not reject cross-user write'; END IF;
  IF NOT EXISTS (SELECT 1 FROM roles WHERE name='user') THEN RAISE EXCEPTION 'role seed missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM billing_plans WHERE plan_key='free') THEN RAISE EXCEPTION 'plan seed missing'; END IF;
  IF (SELECT enabled FROM provider_configs WHERE provider_key='local') THEN RAISE EXCEPTION 'optional local provider unexpectedly enabled'; END IF;
END $test$;
ROLLBACK;
