-- Rollback-only assertions run as the separately provisioned non-owner app role.
BEGIN;
SET LOCAL search_path TO ngit, public;
CREATE TEMP TABLE ngit_test_ids (key text PRIMARY KEY, value uuid NOT NULL) ON COMMIT DROP;
-- The fixture setup runs outside forced tenant RLS, while no user context exists.
-- Privileges to insert fixture users are explicitly provisioned only on this disposable database.
RESET ROLE;
INSERT INTO ngit.users(email,password_hash,display_name)
VALUES ('db-test-one@example.invalid','test-only','Test One'),('db-test-two@example.invalid','test-only','Test Two');
INSERT INTO ngit_test_ids(key,value) SELECT 'u1',id FROM ngit.users WHERE email='db-test-one@example.invalid';
INSERT INTO ngit_test_ids(key,value) SELECT 'u2',id FROM ngit.users WHERE email='db-test-two@example.invalid';
SET LOCAL ROLE CURRENT_USER;
DO $test$
DECLARE u1 uuid; u2 uuid; c1 uuid; p1 uuid; a1 uuid; plan_id uuid; sub_id uuid; visible_count integer; rejected boolean;
BEGIN
 SELECT value INTO u1 FROM ngit_test_ids WHERE key='u1'; SELECT value INTO u2 FROM ngit_test_ids WHERE key='u2';
 rejected:=false; BEGIN INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('DB-TEST-ONE@example.invalid','test-only','duplicate'); EXCEPTION WHEN unique_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'case-insensitive duplicate email accepted'; END IF;
 PERFORM set_config('ngit.user_id',u1::text,true);
 INSERT INTO ngit.conversations(user_id,title) VALUES (u1,'One') RETURNING id INTO c1;
 INSERT INTO ngit.messages(user_id,conversation_id,role,content) VALUES (u1,c1,'user','hello');
 INSERT INTO ngit.media_assets(user_id,media_type) VALUES (u1,'video') RETURNING id INTO a1;
 INSERT INTO ngit.videos(user_id,source_asset_id,title) VALUES (u1,a1,'owned');
 INSERT INTO ngit.presentations(user_id,title) VALUES (u1,'Deck') RETURNING id INTO p1;
 INSERT INTO ngit.presentation_slides(user_id,presentation_id,position) VALUES (u1,p1,0);
 rejected:=false; BEGIN INSERT INTO ngit.messages(user_id,conversation_id,role,content) VALUES (u1,c1,'invalid','bad role'); EXCEPTION WHEN check_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'invalid message role accepted'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.presentation_slides(user_id,presentation_id,position) VALUES (u1,p1,0); EXCEPTION WHEN unique_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'duplicate slide position accepted'; END IF;
 SELECT id INTO plan_id FROM ngit.billing_plans WHERE plan_key='free';
 IF plan_id IS NULL THEN RAISE EXCEPTION 'free plan seed missing'; END IF;
 INSERT INTO ngit.subscriptions(user_id,plan_id) VALUES (u1,plan_id) RETURNING id INTO sub_id;
 INSERT INTO ngit.usage_records(user_id,subscription_id,metric,quantity) VALUES (u1,sub_id,'requests',1);
 rejected:=false; BEGIN INSERT INTO ngit.usage_records(user_id,subscription_id,metric,quantity) VALUES (u1,sub_id,'requests',-1); EXCEPTION WHEN check_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'negative usage accepted'; END IF;
 IF NOT EXISTS(SELECT 1 FROM ngit.roles WHERE name='user') THEN RAISE EXCEPTION 'user role seed missing'; END IF;
 IF coalesce((SELECT enabled FROM ngit.provider_configs WHERE provider_key='local'),true) THEN RAISE EXCEPTION 'local provider not disabled by default'; END IF;
 SELECT count(*) INTO visible_count FROM ngit.conversations;
 IF visible_count<>1 THEN RAISE EXCEPTION 'expected one owned conversation; got %',visible_count; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.conversations(user_id,title) VALUES (u2,'forbidden'); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'RLS allowed foreign owner insert'; END IF;
 PERFORM set_config('ngit.user_id',u2::text,true);
 SELECT count(*) INTO visible_count FROM ngit.conversations;
 IF visible_count<>0 THEN RAISE EXCEPTION 'tenant scope leaked conversation rows: %',visible_count; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.conversations(user_id,title) VALUES (u2,'Two') RETURNING id INTO c1; EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF rejected THEN RAISE EXCEPTION 'owner conversation insert rejected'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.messages(user_id,conversation_id,role,content) VALUES (u2,(SELECT value FROM ngit_test_ids WHERE key='not-a-conversation'),'user','bad'); EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'invalid conversation reference accepted'; END IF;
END $test$;
ROLLBACK;
