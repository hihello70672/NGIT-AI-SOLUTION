"""HTTP contract tests for identity and user endpoints."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER","test-auth-pepper-value-at-least-32-bytes");os.environ.setdefault("PASSWORD_PEPPER","test-password-pepper-value")
from fastapi.testclient import TestClient
from services.api import app as module
class FakeUsers:
    def __init__(self):self.rows={};self.counter=0
    def create(self,email,password_hash,display_name):
        from psycopg.errors import UniqueViolation
        if self.by_email(email):raise UniqueViolation("duplicate")
        self.counter+=1;row={"id":str(self.counter),"email":email.lower(),"display_name":display_name,"status":"active","roles":["user"],"created_at":"now","password_hash":password_hash};self.rows[row["id"]]=row;return row
    def by_email(self,email):return next((dict(r) for r in self.rows.values() if r["email"]==email.lower()),None)
    def by_id(self,user_id):return dict(self.rows[user_id]) if user_id in self.rows else None
    def update_display_name(self,user_id,name):
        if user_id not in self.rows:return None
        self.rows[user_id]["display_name"]=name;return self.by_id(user_id)
    def list_users(self,limit=100,offset=0):return [dict(r) for r in list(self.rows.values())[offset:offset+limit]]
def setup():
    fake=FakeUsers();module.users=fake;module.auth.users=fake
    module.authenticator,module.policies,module.approvals,module.audit,module.emergency,module.actions=module.create_default_security();module.auth.authenticator=module.authenticator
    return fake
def test_auth_profile_logout():
    setup()
    with TestClient(module.app) as c:
        response=c.post("/api/v1/auth/register",json={"email":"Person@example.com","password":"long-enough-password","display_name":"Person"});assert response.status_code==201
        headers={"Authorization":f"Bearer {response.json()['access_token']}"}
        assert c.get("/api/v1/users/me",headers=headers).json()["email"]=="person@example.com"
        assert c.patch("/api/v1/users/me",headers=headers,json={"display_name":"Updated"}).json()["display_name"]=="Updated"
        assert c.post("/api/v1/auth/logout",headers=headers).status_code==204
        assert c.get("/api/v1/users/me",headers=headers).status_code==401
def test_login_admin_and_validation():
    fake=setup()
    with TestClient(module.app) as c:
        payload={"email":"user@example.com","password":"long-enough-password","display_name":"User"}
        assert c.post("/api/v1/auth/login",json=payload).status_code==401
        created=c.post("/api/v1/auth/register",json=payload).json();headers={"Authorization":f"Bearer {created['access_token']}"}
        assert c.get("/api/v1/users",headers=headers).status_code==403
        assert c.patch("/api/v1/users/me",headers=headers,json={}).status_code==422
        assert c.get("/api/v1/users",headers=headers,params={"limit":101}).status_code==422
        admin=fake.create("admin@example.com","unused","Admin");admin["roles"]=["admin"];fake.rows[admin["id"]]=admin
        token=module.authenticator.issue(admin["id"],{"admin"});listing=c.get("/api/v1/users",headers={"Authorization":f"Bearer {token}"})
        assert listing.status_code==200 and len(listing.json()["users"])==2
def test_request_id_error_contract():
    with TestClient(module.app) as c:
        r=c.post("/api/v1/auth/register",headers={"X-Request-ID":"bad id"},json={})
        assert r.status_code==422 and r.headers["X-Request-ID"]!="bad id" and r.json()["error"]["request_id"]==r.headers["X-Request-ID"]
def test_memory_routes_use_authenticated_context():
    paths={route.path for route in module.app.routes}
    assert "/api/v1/conversations" in paths
    assert "/api/v1/memories/search" in paths
    with TestClient(module.app) as c: assert c.get("/api/v1/conversations").status_code==401
