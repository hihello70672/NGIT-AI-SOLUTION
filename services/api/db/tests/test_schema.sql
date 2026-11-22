-- Run on a fresh disposable DB using a provisioned, non-owner, non-superuser app role.
BEGIN;
CREATE TEMP TABLE ngit_test_ids(key text PRIMARY KEY,value uuid NOT NULL) ON COMMIT DROP;
DO $fixtures$
DECLARE u1 uuid; u2 uuid; rejected boolean;
BEGIN
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
 PERFORM set_config('ngit.user_id',u1::text,true);
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
 INSERT INTO ngit_test_ids VALUES ('u1',u1),('u2',u2);
 rejected:=false; BEGIN INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('DB-TEST-ONE@example.invalid','test-only','duplicate'); EXCEPTION WHEN unique_violation THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'case-insensitive duplicate email accepted'; END IF;
END $fixtures$;
DO $admin$ DECLARE u1 uuid; u2 uuid; role_id uuid; rejected boolean;
BEGIN
 SELECT value INTO u1 FROM ngit_test_ids WHERE key='u1'; SELECT value INTO u2 FROM ngit_test_ids WHERE key='u2';
 SELECT id INTO role_id FROM ngit.roles WHERE name='admin';
 INSERT INTO ngit.user_roles(user_id,role_id) VALUES(u1,role_id);
 PERFORM set_config('ngit.user_id',u1::text,true);
 INSERT INTO ngit.admin_rules(action,roles,approval_required,restricted,updated_by) VALUES ('test.admin.rule',ARRAY['admin'],true,true,u1);
 INSERT INTO ngit.service_controls(service,enabled,updated_by) VALUES ('test-api',false,u1);
 IF (SELECT count(*) FROM ngit.admin_rules WHERE action='test.admin.rule')<>1 THEN RAISE EXCEPTION 'admin rule unavailable to admin'; END IF;
 IF (SELECT count(*) FROM ngit.service_controls WHERE service='test-api')<>1 THEN RAISE EXCEPTION 'service state unavailable to admin'; END IF;
 PERFORM set_config('ngit.user_id',u2::text,true);
 IF (SELECT count(*) FROM ngit.admin_rules WHERE action='test.admin.rule')<>0 THEN RAISE EXCEPTION 'admin rule visible to non-admin'; END IF;
 IF (SELECT count(*) FROM ngit.service_controls WHERE service='test-api')<>0 THEN RAISE EXCEPTION 'service state visible to non-admin'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.admin_rules(action,roles,updated_by) VALUES('unauthorized.rule',ARRAY['user'],u2); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'non-admin inserted admin rule'; END IF;
END $admin$;
ROLLBACK;
