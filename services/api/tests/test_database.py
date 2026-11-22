from contextlib import contextmanager

import pytest

from services.api.database import Database


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnection:
    def __init__(self):
        self.calls = []

    def transaction(self):
        return FakeTransaction()

    def execute(self, query, params=None):
        self.calls.append((query, params))
        return self

    def fetchone(self):
        return (1,)


class FakePool:
    def __init__(self, conn):
        self.conn = conn

    @contextmanager
    def connection(self):
        yield self.conn


def test_user_context_is_transaction_local():
    db = Database("postgresql://unused", "ngit")
    conn = FakeConnection()
    db.pool = FakePool(conn)
    with db.connection("user-123"):
        pass
    assert conn.calls == [("SELECT set_config('ngit.user_id', %s, true)", ("user-123",))]


def test_anonymous_connection_does_not_set_rls_identity():
    db = Database("postgresql://unused", "ngit")
    conn = FakeConnection()
    db.pool = FakePool(conn)
    with db.connection():
        pass
    assert conn.calls == []


def test_schema_and_user_context_are_validated():
    with pytest.raises(ValueError, match="schema"):
        Database("postgresql://unused", "bad-name")
    db = Database("postgresql://unused")
    with pytest.raises(ValueError, match="user context"):
        with db.connection(" "):
            pass
