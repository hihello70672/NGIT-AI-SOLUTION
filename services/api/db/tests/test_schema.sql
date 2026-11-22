-- Rollback-only checks through a separately provisioned non-owner app login.
BEGIN;
SET search_path TO ngit, public;
DO $test$
DECLARE u1 uuid; u2 uuid; c1 uuid; c2 uuid; p1 uuid; a1 uuid; plan_id uuid; sub_id uuid; visible_count integer; rejected boolean;
BEGIN
 -- Insert fixture identities while no user context is set; FORCE RLS masks reads, not inserts absent a policy.
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('db-test-one@example.invalid','test-only','Test One') RETURNING id INTO u1;
 INSERT INTO ngit.users(email,password_hash,display_name) VALUES ('db-test-two@example.invalid','test-only','Test Two') RETURNING id INTO u2;
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
 -- As user one, an explicit foreign owner value must fail WITH CHECK.
 rejected:=false; BEGIN INSERT INTO ngit.conversations(user_id,title) VALUES (u2,'forbidden'); EXCEPTION WHEN insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'RLS allowed cross-owner conversation insert'; END IF;
 -- A row belonging to another tenant cannot be read or mutated under user one's context.
 PERFORM set_config('ngit.user_id',u2::text,true);
 INSERT INTO ngit.conversations(user_id,title) VALUES (u2,'Two') RETURNING id INTO c2;
 SELECT count(*) INTO visible_count FROM ngit.conversations;
 IF visible_count<>1 THEN RAISE EXCEPTION 'tenant scope failed for second owner: %',visible_count; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.messages(user_id,conversation_id,role,content) VALUES (u2,c1,'user','foreign conversation'); EXCEPTION WHEN foreign_key_violation OR insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant message accepted'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.videos(user_id,source_asset_id,title) VALUES (u2,a1,'foreign asset'); EXCEPTION WHEN foreign_key_violation OR insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant video source accepted'; END IF;
 rejected:=false; BEGIN INSERT INTO ngit.presentation_slides(user_id,presentation_id,position) VALUES (u2,p1,1); EXCEPTION WHEN foreign_key_violation OR insufficient_privilege THEN rejected:=true; END;
 IF NOT rejected THEN RAISE EXCEPTION 'cross-tenant slide accepted'; END IF;
END $test$;
ROLLBACK;
