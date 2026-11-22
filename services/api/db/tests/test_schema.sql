-- Run on a fresh disposable database and application login.
BEGIN;
CREATE TEMP TABLE ngit_test_ids(key text PRIMARY KEY,value uuid NOT NULL) ON COMMIT DROP;
DO $setup$ DECLARE u1 uuid; u2 uuid; BEGIN
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES('schema-admin@example.invalid','test-only','Schema Admin') RETURNING id INTO u1;
 PERFORM set_config('ngit.user_id',u1::text,true);
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES('schema-user@example.invalid','test-only','Schema User') RETURNING id INTO u2;
 INSERT INTO ngit_test_ids VALUES('admin',u1),('user',u2);
END $setup$;
DO $checks$ DECLARE admin_id uuid; user_id uuid; role_id uuid; rejected boolean;
BEGIN
 SELECT value INTO admin_id FROM ngit_test_ids WHERE key='admin'; SELECT value INTO user_id FROM ngit_test_ids WHERE key='user'; SELECT id INTO role_id FROM ngit.roles WHERE name='admin';
 INSERT INTO ngit.user_roles(user_id,role_id) VALUES(admin_id,role_id);
 PERFORM set_config('ngit.user_id',admin_id::text,true);
 INSERT INTO ngit.admin_rules(action,roles,approval_required,restricted,updated_by) VALUES('schema.test.rule',ARRAY['admin'],true,true,admin_id);
 INSERT INTO ngit.service_controls(service,enabled,updated_by) VALUES('schema-test',false,admin_id);
 IF (SELECT count(*) FROM ngit.users WHERE id=user_id)<>1 THEN RAISE EXCEPTION 'admin cannot list users'; END IF;
 PERFORM set_config('ngit.user_id',user_id::text,true);
 IF (SELECT count(*) FROM ngit.admin_rules WHERE action='schema.test.rule')<>0 OR (SELECT count(*) FROM ngit.service_controls WHERE service='schema-test')<>0 THEN RAISE EXCEPTION 'admin state visible to regular user'; END IF;
 IF (SELECT count(*) FROM ngit.users WHERE id=admin_id)<>0 THEN RAISE EXCEPTION 'regular user can list other users'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.admin_rules(action,roles,updated_by) VALUES('schema.denied.rule',ARRAY['user'],user_id); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'non-admin inserted admin rule'; END IF;
END $checks$;
ROLLBACK;
