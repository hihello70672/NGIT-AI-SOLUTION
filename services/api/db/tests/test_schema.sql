-- Transactional integration assertions; apply migrations first, then run as a
-- non-superuser and non-table-owner role with the fixture DML privileges described in README.
BEGIN;
SET search_path TO ngit,public;
DO $test$
DECLARE
  u1 uuid; u2 uuid; c1 uuid; p1 uuid; a1 uuid;
  visible_count integer; rejected boolean := false; plan_id uuid; sub_id uuid;
  duplicate_rejected boolean := false; invalid_rejected boolean := false;
BEGIN
  INSERT INTO users(email,password_hash,display_name) VALUES
    ('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
  INSERT INTO users(email,password_hash,display_name) VALUES
    ('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
  rejected := false;
  BEGIN INSERT INTO users(email,password_hash,display_name) VALUES('DB-TEST-ONE@example.invalid','test-only','duplicate');
  EXCEPTION WHEN unique_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'case-insensitive duplicate email accepted'; END IF;

  INSERT INTO conversations(user_id,title) VALUES(u1,'One') RETURNING id INTO c1;
  INSERT INTO conversations(user_id,title) VALUES(u2,'Two');
  INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'user','hello');
  rejected := false;
  BEGIN INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u2,c1,'user','cross tenant');
  EXCEPTION WHEN foreign_key_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant message FK accepted'; END IF;
  rejected := false;
  BEGIN INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'unknown','bad role');
  EXCEPTION WHEN check_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'invalid message role accepted'; END IF;

  INSERT INTO media_assets(user_id,media_type) VALUES(u1,'video') RETURNING id INTO a1;
  INSERT INTO videos(user_id,source_asset_id,title) VALUES(u1,a1,'owned');
  rejected := false;
  BEGIN INSERT INTO videos(user_id,source_asset_id,title) VALUES(u2,a1,'cross tenant');
  EXCEPTION WHEN foreign_key_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant video asset FK accepted'; END IF;

  INSERT INTO presentations(user_id,title) VALUES(u1,'Deck') RETURNING id INTO p1;
  INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u1,p1,0);
  rejected := false;
  BEGIN INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u2,p1,1);
  EXCEPTION WHEN foreign_key_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant slide FK accepted'; END IF;
  rejected := false;
  BEGIN INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u1,p1,0);
  EXCEPTION WHEN unique_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'duplicate slide position accepted'; END IF;

  SELECT id INTO plan_id FROM billing_plans WHERE plan_key='free';
  IF plan_id IS NULL THEN RAISE EXCEPTION 'free plan seed missing'; END IF;
  INSERT INTO subscriptions(user_id,plan_id) VALUES(u1,plan_id) RETURNING id INTO sub_id;
  INSERT INTO usage_records(user_id,subscription_id,metric,quantity) VALUES(u1,sub_id,'requests',1);
  rejected := false;
  BEGIN INSERT INTO usage_records(user_id,subscription_id,metric,quantity) VALUES(u1,sub_id,'requests',-1);
  EXCEPTION WHEN check_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'negative usage accepted'; END IF;
  IF NOT EXISTS(SELECT 1 FROM roles WHERE name='user') THEN RAISE EXCEPTION 'user role seed missing'; END IF;
  IF COALESCE((SELECT enabled FROM provider_configs WHERE provider_key='local'),true) THEN RAISE EXCEPTION 'local provider must default disabled'; END IF;

  PERFORM set_config('ngit.user_id',u1::text,true);
  SELECT count(*) INTO visible_count FROM conversations;
  IF visible_count<>1 THEN RAISE EXCEPTION 'expected one owner conversation, got %',visible_count; END IF;
  SELECT count(*) INTO visible_count FROM memories;
  IF visible_count<>0 THEN RAISE EXCEPTION 'unexpected visible memory rows'; END IF;
  rejected := false;
  BEGIN INSERT INTO conversations(user_id,title) VALUES(u2,'forbidden');
  EXCEPTION WHEN insufficient_privilege THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'RLS allowed cross-owner insert'; END IF;
  rejected := false;
  BEGIN INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u2,p1,2);
  EXCEPTION WHEN insufficient_privilege OR foreign_key_violation THEN rejected := true; END;
  IF NOT rejected THEN RAISE EXCEPTION 'cross-owner slide write accepted'; END IF;
END $test$;
ROLLBACK;
