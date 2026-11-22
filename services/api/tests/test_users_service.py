from datetime import datetime, timezone
import pytest
from services.api.services.users import UserService

class Result:
    def __init__(self, row=None, rows=None): self.row, self.rows = row, rows or []
    def fetchone(self): return self.row
    def fetchall(self): return self.rows
class Connection:
    def __init__(self, results): self.results, self.calls = iter(results), []
    def execute(self, query, params=()):
        self.calls.append((query, params))
        return next(self.results)
class Database:
    def __init__(self, conn): self.conn, self.contexts = conn, []
    def connection(self, user_id=None):
        self.contexts.append(user_id)
        return self
    def __enter__(self): return self.conn
    def __exit__(self, *_): return False

def test_user_lookup_maps_identity_roles_and_hides_password_hash():
    now = datetime.now(timezone.utc)
    conn = Connection([Result(("id-1", "person@example.com", "Person", "active", now, ["user"]))])
    db = Database(conn)
    user = UserService(db).by_id("id-1")
    assert user["id"] == "id-1" and user["roles"] == ["user"]
    assert "password_hash" not in user
    assert db.contexts == ["id-1"]

def test_profile_update_loads_roles_inside_owner_context():
    now = datetime.now(timezone.utc)
    conn = Connection([Result(("id-1", "person@example.com", "New", "active", now)), Result(rows=[("user",)])])
    db = Database(conn)
    assert UserService(db).update_display_name("id-1", "New")["roles"] == ["user"]
    assert db.contexts == ["id-1"]

def test_admin_user_list_is_bounded_and_hides_password_hash():
    conn = Connection([Result(rows=[])])
    db = Database(conn)
    service = UserService(db)
    assert service.list_users(10, 2) == []
    assert "password_hash" not in conn.calls[0][0]
    with pytest.raises(ValueError): service.list_users(101, 0)
    assert db.contexts == [None]

def test_registration_user_and_role_are_created_atomically():
    now = datetime.now(timezone.utc)
    conn = Connection([Result(("id-1", "person@example.com", "Person", "active", now)), Result(("role-id",)), Result()])
    user = UserService(Database(conn)).create("Person@example.com", "encoded", "Person")
    assert user["roles"] == ["user"] and user["password_hash"] == "encoded"
    assert conn.calls[-1][1] == ("id-1", "role-id")
    assert "ON CONFLICT DO NOTHING" in conn.calls[-1][0]

def test_email_lookup_normalizes_email():
    conn = Connection([Result(("id-1", "person@example.com", "hash", "Person", "active", datetime.now(timezone.utc), ["user"]))])
    UserService(Database(conn)).by_email("PERSON@example.com")
    assert conn.calls[0][1] == ("person@example.com",)
