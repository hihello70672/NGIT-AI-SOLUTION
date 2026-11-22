"""API behavior tests using an isolated in-memory service boundary."""
import os
os.environ.setdefault("AUTH_TOKEN_PEPPER", "test-auth-pepper-value-at-least-32-bytes")
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from services.api import app as api

class FakeUsers:
    def __init__(self): self.rows={}; self.next=0
    def create(self,email,password_hash,display_name):
        self.next+=1
        row={"id":str(self.next),"email":email,"password_hash":password_hash,"display_name":display_name,"status":"active","roles":["user"],"created_at":datetime.now(timezone.utc)}
        self.rows[row["id"]]=row
        return row.copy()
    def by_email(self,email):
        return next((r.copy() for r in self.rows.values() if r["email"]==email.lower()),None)
    def by_id(self,user_id):
        row=self.rows.get(user_id)
        return row.copy() if row else None
    def update_display_name(self,user_id,name):
        if user_id not in self.rows:return None
        self.rows[user_id]["display_name"]=name
        return self.rows[user_id].copy()

api.users=FakeUsers()
api.auth=api.AuthService(api.users,api.authenticator)
client=TestClient(api.app)

def test_registration_profile_and_logout():
    response=client.post("/api/v1/auth/register",json={"email":"a@example.com","password":"long-enough-password","display_name":"A"})
    assert response.status_code==201
    token=response.json()["access_token"]
    headers={"Authorization":f"Bearer {token}"}
    assert client.get("/api/v1/users/me",headers=headers).json()["email"]=="a@example.com"
    assert client.patch("/api/v1/users/me",headers=headers,json={"display_name":"Ada"}).json()["display_name"]=="Ada"
    assert client.post("/api/v1/auth/logout",headers=headers).status_code==204
    assert client.get("/api/v1/users/me",headers=headers).status_code==401

def test_validation_and_auth_errors():
    assert client.post("/api/v1/auth/register",json={"email":"bad","password":"x","display_name":""}).status_code==422
    response=client.get("/api/v1/users/me")
    assert response.status_code==401 and response.json()["error"]["code"]=="unauthenticated"
