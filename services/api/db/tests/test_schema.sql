-- Transactional integration checks; run as non-superuser, non-table-owner role.
BEGIN;
SET search_path TO ngit,public;
DO $test$
DECLARE u1 uuid;u2 uuid;c1 uuid;p1 uuid;a1 uuid;seen integer;rejected boolean:=false;planid uuid;subid uuid;
BEGIN
 INSERT INTO users(email,password_hash,display_name) VALUES('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
 INSERT INTO users(email,password_hash,display_name) VALUES('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
 INSERT INTO conversations(user_id,title) VALUES(u1,'One') RETURNING id INTO c1;
 INSERT INTO conversations(user_id,title) VALUES(u2,'Two');
 INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'user','hello');
 BEGIN INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u2,c1,'user','cross owner'); EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-owner message FK not rejected'; END IF;
 INSERT INTO media_assets(user_id,media_type) VALUES(u1,'video') RETURNING id INTO a1;
 INSERT INTO videos(user_id,source_asset_id,title) VALUES(u1,a1,'owned');
 BEGIN INSERT INTO videos(user_id,source_asset_id,title) VALUES(u2,a1,'cross owner'); EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-owner asset FK not rejected'; END IF;
 INSERT INTO presentations(user_id,title) VALUES(u1,'Deck') RETURNING id INTO p1;
 INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u1,p1,0);
 BEGIN INSERT INTO presentation_slides(user_id,presentation_id,position) VALUES(u2,p1,1); EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-owner slide FK not rejected'; END IF;
 SELECT id INTO planid FROM billing_plans WHERE plan_key='free';
 INSERT INTO subscriptions(user_id,plan_id) VALUES(u1,planid) RETURNING id INTO subid;
 INSERT INTO usage_records(user_id,subscription_id,metric,quantity) VALUES(u1,subid,'requests',1);
 PERFORM set_config('ngit.user_id',u1::text,true);
 SELECT count(*) INTO seen FROM conversations; IF seen<>1 THEN RAISE EXCEPTION 'RLS expected one conversation, got %',seen; END IF;
 SELECT count(*) INTO seen FROM memories; IF seen<>0 THEN RAISE EXCEPTION 'unexpected memory rows'; END IF;
 rejected:=false; BEGIN INSERT INTO conversations(user_id,title) VALUES(u2,'forbidden'); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'RLS allowed cross-owner write'; END IF;
 IF NOT EXISTS(SELECT 1 FROM roles WHERE name='user') THEN RAISE EXCEPTION 'user role seed missing'; END IF;
 IF NOT EXISTS(SELECT 1 FROM billing_plans WHERE plan_key='free') THEN RAISE EXCEPTION 'free plan seed missing'; END IF;
 IF COALESCE((SELECT enabled FROM provider_configs WHERE provider_key='local'),true) THEN RAISE EXCEPTION 'local provider must default disabled'; END IF;
END $test$;
ROLLBACK;
