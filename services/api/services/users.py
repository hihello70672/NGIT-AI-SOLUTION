"""Identity and user-management persistence operations."""
from typing import Any
from psycopg.rows import dict_row

class UserService:
    def __init__(self, database: Any) -> None:
        self.database = database

    def create(self, email: str, password_hash: str, display_name: str) -> dict:
        with self.database.connection() as conn:
            row = conn.execute("""INSERT INTO users(email,password_hash,display_name) VALUES (%s,%s,%s)
                RETURNING id,email,display_name,status,created_at""", (email.lower(), password_hash, display_name)).fetchone()
            if row is None:
                raise RuntimeError("user creation returned no row")
            user = dict(row) if isinstance(row, dict) else dict(zip(("id","email","display_name","status","created_at"), row))
            role = conn.execute("SELECT id FROM roles WHERE name='user'").fetchone()
            if role:
                conn.execute("INSERT INTO user_roles(user_id,role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (user["id"], role[0] if not isinstance(role, dict) else role["id"]))
            return user

    def by_email(self, email: str) -> dict | None:
        with self.database.connection() as conn:
            cur = conn.execute("""SELECT u.id,u.email,u.password_hash,u.display_name,u.status,u.created_at,
                COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::text[]) AS roles
                FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id
                WHERE u.email=%s GROUP BY u.id""", (email.lower(),))
            row = cur.fetchone()
            if row is None: return None
            if isinstance(row, dict): return row
            return dict(zip(("id","email","password_hash","display_name","status","created_at","roles"), row))

    def by_id(self, user_id: str) -> dict | None:
        with self.database.connection(user_id) as conn:
            row = conn.execute("""SELECT u.id,u.email,u.display_name,u.status,u.created_at,
                COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::text[]) AS roles
                FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id
                WHERE u.id=%s GROUP BY u.id""", (user_id,)).fetchone()
            if row is None: return None
            return row if isinstance(row, dict) else dict(zip(("id","email","display_name","status","created_at","roles"), row))

    def update_display_name(self, user_id: str, display_name: str) -> dict | None:
        with self.database.connection(user_id) as conn:
            row = conn.execute("UPDATE users SET display_name=%s,updated_at=now() WHERE id=%s AND status='active' RETURNING id,email,display_name,status,created_at", (display_name,user_id)).fetchone()
            if row is None: return None
            user = row if isinstance(row, dict) else dict(zip(("id","email","display_name","status","created_at"), row))
            roles = conn.execute("SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id=%s ORDER BY r.name", (user_id,)).fetchall()
            user["roles"] = [r[0] if not isinstance(r,dict) else r["name"] for r in roles]
            return user
