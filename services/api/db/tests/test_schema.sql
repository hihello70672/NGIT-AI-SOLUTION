-- Run on an empty disposable database as a non-superuser, non-owner role.
BEGIN;
SET search_path TO ngit,public;
DO $test$
DECLARE u1 uuid; u2 uuid; c1 uuid; p1 uuid; a1 uuid; seen integer; rejected boolean:=false;
BEGIN
 INSERT INTO users(email,password_hash,display_name) VALUES ('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
 INSERT INTO users(email,password_hash,display_name) VALUES ('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
 INSERT INTO conversations(user_id,title) VALUES(u1,'One') RETURNING id INTO c1;
 INSERT INTO conversations(user_id,title) VALUES(u2,'Two');
 INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'user','hello');
 BEGIN INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u2,c1,'user','cross owner');
 EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-owner message FK was not rejected'; END IF;
 INSERT INTO media_assets(user_id,media_type) VALUES(u1,'video') RETURNING id INTO a1;
 INSERT INTO videos(user_id,source_asset_id,title) VALUES(u1,a1,'owned');
 INSERT INTO presentations(user_id,title) VALUES(u1,'Deck') RETURNING id INTO p1;
 INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u1,p1,0);
 PERFORM set_config('ngit.user_id',u1::text,true);
 SELECT count(*) INTO seen FROM conversations;
 IF seen<>1 THEN RAISE EXCEPTION 'RLS expected one conversation, saw %',seen; END IF;
 rejected:=false;
 BEGIN INSERT INTO conversations(user_id,title) VALUES(u2,'forbidden');
 EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'RLS allowed cross-owner insert'; END IF;
 IF NOT EXISTS(SELECT 1 FROM roles WHERE name='user') THEN RAISE EXCEPTION 'role seed missing'; END IF;
 IF NOT EXISTS(SELECT 1 FROM billing_plans WHERE plan_key='free') THEN RAISE EXCEPTION 'billing plan seed missing'; END IF;
 IF COALESCE((SELECT enabled FROM provider_configs WHERE provider_key='local'),true) THEN RAISE EXCEPTION 'local provider must be opt-in'; END IF;
END $test$;
ROLLBACK;
