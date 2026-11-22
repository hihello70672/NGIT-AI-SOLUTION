"""Psycopg pool adapter with transaction-local authenticated RLS context."""
from contextlib import contextmanager
from typing import Iterator, Any

from psycopg_pool import ConnectionPool


class Database:
    def __init__(self, dsn: str, schema: str = "ngit") -> None:
        if not schema.replace("_", "").isalnum() or not schema[0].isalpha():
            raise ValueError("invalid database schema")
        self.schema = schema
        self.pool = ConnectionPool(conninfo=dsn, open=False,
                                   kwargs={"options": f"-c search_path={schema},public"}, row_factory=None)

    def open(self) -> None:
        self.pool.open(wait=True)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def connection(self, user_id: str | None = None) -> Iterator[Any]:
        """Yield a transactional connection; set RLS identity locally, never per session."""
        with self.pool.connection() as conn:
            with conn.transaction():
                if user_id is not None:
                    if not isinstance(user_id, str) or not user_id or len(user_id) > 256:
                        raise ValueError("invalid database user context")
                    conn.execute("SELECT set_config('ngit.user_id', %s, true)", (user_id,))
                yield conn

    def healthcheck(self) -> bool:
        with self.connection() as conn:
            return conn.execute("SELECT 1").fetchone()[0] == 1


__all__ = ["Database"]
