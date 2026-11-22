"""Identity and user-management persistence operations."""
from typing import Any

class UserService:
    def __init__(self, database: Any) -> None:
        self.database = database

    @staticmethod
    def _mapping(row, keys: tuple[str, ...]) -> dict:
        if isinstance(row, dict):
            return dict(row)
        return dict(zip(keys, row))

    def create(self, email: str, password_hash: str, display_name: str) -> dict:
        with self.database.connection() as conn:
            row = conn.execute("""INSERT INTO users(email,password_hash,display_name) VALUES (%s,%s,%s)
                RETURNING id,email,display_name,status,created_at""", (email.lower(), password_hash, display_name)).fetchone()
            if row is None:
                raise RuntimeError("user creation returned no row")
            user = self._mapping(row, ("id","email","display_name","status","created_at"))
            role = conn.execute("SELECT id FROM roles WHERE name='user'").fetchone()
            if role:
                role_id = role["id"] if isinstance(role, dict) else role[0]
                conn.execute("INSERT INTO user_roles(user_id,role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (user["id"], role_id))
            user["roles"] = ["user"] if role else []
            return user

    def by_email(self, email: str) -> dict | None:
        with self.database.connection() as conn:
            cur = conn.execute("""SELECT u.id,u.email,u.password_hash,u.display_name,u.status,u.created_at,
                COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::text[]) AS roles
                FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id
                WHERE u.email=%s GROUP BY u.id""", (email.lower(),))
            row = cur.fetchone()
            return None if row is None else self._mapping(row, ("id","email","password_hash","display_name","status","created_at","roles"))

    def by_id(self, user_id: str) -> dict | None:
        with self.database.connection(user_id) as conn:
            row = conn.execute("""SELECT u.id,u.email,u.display_name,u.status,u.created_at,
                COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::text[]) AS roles
                FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id
                WHERE u.id=%s GROUP BY u.id""", (user_id,)).fetchone()
            return None if row is None else self._mapping(row, ("id","email","display_name","status","created_at","roles"))

    def update_display_name(self, user_id: str, display_name: str) -> dict | None:
        with self.database.connection(user_id) as conn:
            row = conn.execute("UPDATE users SET display_name=%s,updated_at=now() WHERE id=%s AND status='active' RETURNING id,email,display_name,status,created_at", (display_name,user_id)).fetchone()
            if row is None:
                return None
            user = self._mapping(row, ("id","email","display_name","status","created_at"))
            roles = conn.execute("SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id=%s ORDER BY r.name", (user_id,)).fetchall()
            user["roles"] = [r["name"] if isinstance(r,dict) else r[0] for r in roles]
            return user
