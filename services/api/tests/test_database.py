"""Tests for transaction-local database caller context."""
from contextlib import contextmanager

from services.api.database import Database


def test_caller_context_is_transaction_local_and_validated():
    class Connection:
        def __init__(self): self.calls = []
        @contextmanager
        def transaction(self): yield self
        def execute(self, query, params=()): self.calls.append((query, params))
    class Pool:
        def __init__(self): self.conn = Connection()
        @contextmanager
        def connection(self): yield self.conn
    db = Database.__new__(Database)
    db.pool = Pool()
    with db.connection("user-1") as conn:
        assert conn is db.pool.conn
    assert db.pool.conn.calls == [("SELECT set_config('ngit.user_id', %s, true)", ("user-1",))]
