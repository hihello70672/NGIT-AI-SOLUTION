"""Small psycopg pool adapter with explicit user-scoped RLS context."""
from contextlib import contextmanager
from typing import Iterator, Any
from psycopg_pool import ConnectionPool

class Database:
    def __init__(self, dsn: str, schema: str = "ngit") -> None:
        if not schema.replace("_", "").isalnum() or not schema[0].isalpha():
            raise ValueError("invalid database schema")
        self.pool = ConnectionPool(conninfo=dsn, open=False, kwargs={"options": f"-c search_path={schema},public"}, row_factory=None)

    def open(self) -> None:
        self.pool.open(wait=True)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def connection(self, user_id: str | None = None) -> Iterator[Any]:
        with self.pool.connection() as conn:
            with conn.transaction():
                if user_id:
                    conn.execute("SELECT set_config('ngit.user_id', %s, true)", (user_id,))
                yield conn
