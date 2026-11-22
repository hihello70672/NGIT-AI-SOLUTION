-- Disposable database integration checks; transactions roll back all fixture rows.
BEGIN;
SET search_path TO ngit,public;
DO $test$
DECLARE u1 uuid;u2 uuid;c1 uuid;c2 uuid;rejected boolean:=false;visible_count integer;
BEGIN
 INSERT INTO users(email,password_hash,display_name) VALUES('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
 INSERT INTO users(email,password_hash,display_name) VALUES('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
 INSERT INTO conversations(user_id,title) VALUES(u1,'One') RETURNING id INTO c1;
 INSERT INTO conversations(user_id,title) VALUES(u2,'Two') RETURNING id INTO c2;
 INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u1,c1,'user','hello');
 BEGIN INSERT INTO messages(user_id,conversation_id,role,content) VALUES(u2,c1,'user','cross owner'); EXCEPTION WHEN foreign_key_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-owner message FK was not rejected'; END IF;
 PERFORM set_config('ngit.user_id',u1::text,true);
 SELECT count(*) INTO visible_count FROM conversations;
 IF visible_count<>1 THEN RAISE EXCEPTION 'RLS expected one visible row, got %',visible_count; END IF;
 rejected:=false;
 BEGIN INSERT INTO conversations(user_id,title) VALUES(u2,'forbidden'); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'RLS write isolation did not reject'; END IF;
 IF NOT EXISTS(SELECT 1 FROM roles WHERE name='user') THEN RAISE EXCEPTION 'user role seed missing'; END IF;
 IF NOT EXISTS(SELECT 1 FROM billing_plans WHERE plan_key='free') THEN RAISE EXCEPTION 'free plan seed missing'; END IF;
 IF (SELECT enabled FROM provider_configs WHERE provider_key='local') THEN RAISE EXCEPTION 'optional provider unexpectedly enabled'; END IF;
END $test$;
ROLLBACK;
