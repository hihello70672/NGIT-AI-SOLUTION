from datetime import datetime, timezone

import pytest

from services.api.services.users import UserService


class Result:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return next(self.results)


class Database:
    def __init__(self, conn):
        self.conn = conn
        self.contexts = []

    def connection(self, user_id=None):
        self.contexts.append(user_id)
        return self

    def __enter__(self):
        return self.conn

    def __exit__(self, *_):
        return False


def test_user_lookup_maps_identity_and_roles():
    now = datetime.now(timezone.utc)
    conn = Connection([Result(("id-1", "person@example.com", "hash", "Person", "active", now, ["user"]))])
    user = UserService(Database(conn)).by_email("PERSON@example.com")
    assert user["id"] == "id-1"
    assert user["roles"] == ["user"]
    assert "password_hash" in user
    assert conn.calls[0][1] == ("person@example.com",)


def test_profile_read_hides_password_hash_and_paginates():
    now = datetime.now(timezone.utc)
    conn = Connection([Result(("id-1", "person@example.com", "Person", "active", now, ["user"])) , Result(rows=[])])
    db = Database(conn)
    service = UserService(db)
    assert "password_hash" not in service.by_id("id-1")
    assert service.list_users(limit=10, offset=0) == []
    assert db.contexts == [None, None]


def test_pagination_rejects_invalid_values_before_database_access():
    db = Database(Connection([]))
    with pytest.raises(ValueError):
        UserService(db).list_users(limit=101)
    assert db.contexts == []
