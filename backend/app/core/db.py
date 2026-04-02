from __future__ import annotations

import json
import secrets
import sqlite3
import string
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

import psycopg2
import psycopg2.extras
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.schemas import DeviceApprovalRequest

Connection = psycopg2.extensions.connection | sqlite3.Connection


class Database:
    _lock = Lock()

    @property
    def _uses_sqlite(self) -> bool:
        return bool(settings.database_path and not settings.database_url)

    def connect(self) -> Connection:
        if self._uses_sqlite:
            database_path = Path(settings.database_path).expanduser()
            database_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(database_path, timeout=30, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        url = settings.database_url
        if not url:
            raise RuntimeError("DATABASE_URL or KRUD_DATABASE_PATH must be configured")
        # Supabase requires SSL; append sslmode if not already in the URL
        if "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        conn = psycopg2.connect(url)
        psycopg2.extras.register_default_jsonb(conn)
        return conn

    def _row(self, row) -> dict | None:
        """Convert a DB row to a plain dict, serialising datetime → ISO string."""
        if row is None:
            return None
        if isinstance(row, dict):
            raw = dict(row)
        elif hasattr(row, "keys"):
            raw = {key: row[key] for key in row.keys()}
        else:
            raw = dict(row)

        result = {}
        for key, value in raw.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def _execute(
        self,
        conn: Connection,
        query: str,
        params=None,
        *,
        sqlite_query: str | None = None,
        sqlite_params=None,
    ) -> None:
        if self._uses_sqlite:
            cur = conn.cursor()
            cur.execute(
                sqlite_query or query,
                sqlite_params if sqlite_params is not None else (() if params is None else params),
            )
            cur.close()
            return

        with conn.cursor() as cur:
            cur.execute(query, () if params is None else params)

    def _fetchone(
        self,
        conn: Connection,
        query: str,
        params=None,
        *,
        sqlite_query: str | None = None,
        sqlite_params=None,
        dict_row: bool = False,
    ):
        if self._uses_sqlite:
            cur = conn.cursor()
            cur.execute(
                sqlite_query or query,
                sqlite_params if sqlite_params is not None else (() if params is None else params),
            )
            row = cur.fetchone()
            cur.close()
            return self._row(row) if dict_row else row

        cursor_factory = psycopg2.extras.RealDictCursor if dict_row else None
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            cur.execute(query, () if params is None else params)
            row = cur.fetchone()
        return self._row(row) if dict_row else row

    def _fetchall(
        self,
        conn: Connection,
        query: str,
        params=None,
        *,
        sqlite_query: str | None = None,
        sqlite_params=None,
        dict_rows: bool = False,
    ):
        if self._uses_sqlite:
            cur = conn.cursor()
            cur.execute(
                sqlite_query or query,
                sqlite_params if sqlite_params is not None else (() if params is None else params),
            )
            rows = cur.fetchall()
            cur.close()
            return [self._row(row) for row in rows] if dict_rows else rows

        cursor_factory = psycopg2.extras.RealDictCursor if dict_rows else None
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            cur.execute(query, () if params is None else params)
            rows = cur.fetchall()
        return [self._row(row) for row in rows] if dict_rows else rows

    def initialize(self) -> None:
        if not self._uses_sqlite:
            # PostgreSQL schema is managed via Supabase migrations.
            return

        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                create table if not exists users (
                    id text primary key,
                    email text not null unique,
                    name text,
                    password_hash text,
                    subscription_status text not null,
                    trial_ends_at text not null,
                    billing_customer_id text,
                    billing_subscription_id text,
                    created_at text not null
                );

                create table if not exists device_codes (
                    device_code text primary key,
                    user_code text not null unique,
                    client_name text not null,
                    status text not null,
                    created_at text not null,
                    expires_at text not null,
                    email text,
                    name text,
                    session_token text,
                    user_id text
                );

                create table if not exists auth_sessions (
                    token text primary key,
                    user_id text not null,
                    created_at text not null,
                    foreign key (user_id) references users(id) on delete cascade
                );

                create table if not exists chat_sessions (
                    id text primary key,
                    user_id text not null,
                    title text not null,
                    created_at text not null,
                    foreign key (user_id) references users(id) on delete cascade
                );

                create table if not exists chat_messages (
                    id text primary key,
                    session_id text not null,
                    role text not null,
                    content text not null,
                    metadata text not null default '{}',
                    created_at text not null,
                    foreign key (session_id) references chat_sessions(id) on delete cascade
                );

                create table if not exists usage_events (
                    id text primary key,
                    user_id text not null,
                    session_id text,
                    provider text not null,
                    model text not null,
                    prompt_tokens integer not null,
                    completion_tokens integer not null,
                    created_at text not null,
                    foreign key (user_id) references users(id) on delete cascade,
                    foreign key (session_id) references chat_sessions(id) on delete set null
                );

                create index if not exists idx_device_codes_user_code on device_codes(user_code);
                create index if not exists idx_auth_sessions_user_id on auth_sessions(user_id);
                create index if not exists idx_auth_sessions_token on auth_sessions(token);
                create index if not exists idx_chat_sessions_user_id on chat_sessions(user_id);
                create index if not exists idx_chat_messages_session_id on chat_messages(session_id);
                create index if not exists idx_usage_events_user_id on usage_events(user_id);
                create index if not exists idx_users_billing_customer_id on users(billing_customer_id);
                """
            )

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _iso(self, value: datetime) -> str:
        return value.isoformat()

    # ── password auth helpers ──────────────────────────────────────────────────

    def _ensure_password_hash_column(self) -> None:
        """Add password_hash column to existing SQLite DBs that predate this migration."""
        if not self._uses_sqlite:
            return
        with self._lock, self.connect() as conn:
            try:
                conn.execute("alter table users add column password_hash text")
                conn.commit()
            except Exception:
                pass  # Column already exists — normal for new DBs

    def signup_with_password(
        self, email: str, password_hash: str, name: str | None
    ) -> dict:
        """
        Create a new user with email+password, start a trial, and return a session token.
        Raises ValueError if the email is already registered.
        """
        now = self._now()
        user_id = f"user_{secrets.token_hex(8)}"
        trial_ends_at = self._iso(now + timedelta(days=settings.trial_days))
        safe_email = email.strip().lower()

        with self._lock, self.connect() as conn:
            existing = self._fetchone(
                conn,
                "select id from users where email = %s",
                (safe_email,),
                sqlite_query="select id from users where email = ?",
                sqlite_params=(safe_email,),
            )
            if existing is not None:
                raise ValueError("Email already registered")

            self._execute(
                conn,
                """
                insert into users
                    (id, email, name, password_hash, subscription_status,
                     trial_ends_at, billing_customer_id, billing_subscription_id, created_at)
                values (%s, %s, %s, %s, 'trialing', %s, null, null, %s)
                """,
                (user_id, safe_email, name, password_hash, trial_ends_at, self._iso(now)),
                sqlite_query="""
                insert into users
                    (id, email, name, password_hash, subscription_status,
                     trial_ends_at, billing_customer_id, billing_subscription_id, created_at)
                values (?, ?, ?, ?, 'trialing', ?, null, null, ?)
                """,
                sqlite_params=(user_id, safe_email, name, password_hash, trial_ends_at, self._iso(now)),
            )
            token = self._create_session_token(conn, user_id, now)

        return {
            "token": token,
            "user_id": user_id,
            "email": safe_email,
            "name": name,
            "subscription_status": "trialing",
            "trial_ends_at": trial_ends_at,
        }

    def get_user_for_password_auth(self, email: str) -> dict | None:
        """Return the full user row including password_hash for login verification."""
        safe_email = email.strip().lower()
        with self.connect() as conn:
            return self._fetchone(
                conn,
                "select * from users where email = %s",
                (safe_email,),
                sqlite_query="select * from users where email = ?",
                sqlite_params=(safe_email,),
                dict_row=True,
            )

    def create_session_for_user(self, user_id: str) -> str:
        """Create and return a new session token for an existing user."""
        now = self._now()
        with self._lock, self.connect() as conn:
            return self._create_session_token(conn, user_id, now)

    def _create_session_token(self, conn, user_id: str, now: datetime) -> str:
        token = f"krud_{secrets.token_urlsafe(24)}"
        self._execute(
            conn,
            "insert into auth_sessions (token, user_id, created_at) values (%s, %s, %s)",
            (token, user_id, self._iso(now)),
            sqlite_query="insert into auth_sessions (token, user_id, created_at) values (?, ?, ?)",
            sqlite_params=(token, user_id, self._iso(now)),
        )
        return token

    def create_device_code(self, client_name: str) -> dict[str, str]:
        now = self._now()
        record = {
            "device_code": secrets.token_urlsafe(24),
            "user_code": self._generate_user_code(),
            "client_name": client_name,
            "status": "pending",
            "created_at": self._iso(now),
            "expires_at": self._iso(now + timedelta(seconds=settings.device_code_ttl_seconds)),
        }
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                """
                insert into device_codes (device_code, user_code, client_name, status, created_at, expires_at)
                values (%(device_code)s, %(user_code)s, %(client_name)s, %(status)s, %(created_at)s, %(expires_at)s)
                """,
                record,
                sqlite_query="""
                insert into device_codes (device_code, user_code, client_name, status, created_at, expires_at)
                values (:device_code, :user_code, :client_name, :status, :created_at, :expires_at)
                """,
                sqlite_params=record,
            )
        return record

    def complete_device_code(self, user_code: str, approval: DeviceApprovalRequest) -> dict[str, str]:
        now = self._now()
        safe_email = approval.email.lower()
        with self._lock, self.connect() as conn:
            record = self._fetchone(
                conn,
                "select * from device_codes where user_code = %s",
                (user_code,),
                sqlite_query="select * from device_codes where user_code = ?",
                sqlite_params=(user_code,),
                dict_row=True,
            )
            if record is None:
                raise ValueError("Unknown user code")

            expires_at = record["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at <= now:
                self._execute(
                    conn,
                    "update device_codes set status = 'expired' where user_code = %s",
                    (user_code,),
                    sqlite_query="update device_codes set status = 'expired' where user_code = ?",
                    sqlite_params=(user_code,),
                )
                raise ValueError("Device code has expired")

            user = self._fetchone(
                conn,
                "select * from users where email = %s",
                (safe_email,),
                sqlite_query="select * from users where email = ?",
                sqlite_params=(safe_email,),
                dict_row=True,
            )

            if user is None:
                user_id = f"user_{secrets.token_hex(8)}"
                trial_ends_at = self._iso(now + timedelta(days=settings.trial_days))
                self._execute(
                    conn,
                    """
                    insert into users (id, email, name, subscription_status, trial_ends_at,
                        billing_customer_id, billing_subscription_id, created_at)
                    values (%s, %s, %s, 'trialing', %s, null, null, %s)
                    """,
                    (user_id, safe_email, approval.name, trial_ends_at, self._iso(now)),
                    sqlite_query="""
                    insert into users (id, email, name, subscription_status, trial_ends_at,
                        billing_customer_id, billing_subscription_id, created_at)
                    values (?, ?, ?, 'trialing', ?, null, null, ?)
                    """,
                    sqlite_params=(user_id, safe_email, approval.name, trial_ends_at, self._iso(now)),
                )
                subscription_status = "trialing"
                name = approval.name
            else:
                user_id = user["id"]
                subscription_status = user["subscription_status"]
                trial_ends_at = user["trial_ends_at"]
                if isinstance(trial_ends_at, datetime):
                    trial_ends_at = trial_ends_at.isoformat()
                name = user["name"]

            session_token = f"krud_{secrets.token_urlsafe(24)}"
            self._execute(
                conn,
                "insert into auth_sessions (token, user_id, created_at) values (%s, %s, %s)",
                (session_token, user_id, self._iso(now)),
                sqlite_query="insert into auth_sessions (token, user_id, created_at) values (?, ?, ?)",
                sqlite_params=(session_token, user_id, self._iso(now)),
            )
            self._execute(
                conn,
                """
                update device_codes
                set status = 'approved', email = %s, name = %s, session_token = %s, user_id = %s
                where user_code = %s
                """,
                (safe_email, approval.name or name, session_token, user_id, user_code),
                sqlite_query="""
                update device_codes
                set status = 'approved', email = ?, name = ?, session_token = ?, user_id = ?
                where user_code = ?
                """,
                sqlite_params=(safe_email, approval.name or name, session_token, user_id, user_code),
            )
        return {
            "status": "approved",
            "session_token": session_token,
            "user_id": user_id,
            "subscription_status": subscription_status,
            "trial_ends_at": trial_ends_at if isinstance(trial_ends_at, str) else trial_ends_at.isoformat(),
        }

    def poll_device_code(self, device_code: str) -> dict[str, str | None]:
        now = self._now()
        with self.connect() as conn:
            record = self._fetchone(
                conn,
                "select * from device_codes where device_code = %s",
                (device_code,),
                sqlite_query="select * from device_codes where device_code = ?",
                sqlite_params=(device_code,),
                dict_row=True,
            )
            if record is None:
                return {"status": "expired"}

            expires_at = record["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at <= now:
                return {"status": "expired"}
            if record["status"] != "approved":
                return {"status": "pending"}

            user = self._fetchone(
                conn,
                "select * from users where id = %s",
                (record["user_id"],),
                sqlite_query="select * from users where id = ?",
                sqlite_params=(record["user_id"],),
                dict_row=True,
            )

        return {
            "status": "approved",
            "session_token": record["session_token"],
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_status": user["subscription_status"],
            "trial_ends_at": user["trial_ends_at"] if isinstance(user["trial_ends_at"], str) else user["trial_ends_at"].isoformat(),
            "billing_customer_id": user["billing_customer_id"],
            "billing_subscription_id": user["billing_subscription_id"],
        }

    def get_user_by_session_token(self, token: str) -> dict[str, str] | None:
        with self.connect() as conn:
            record = self._fetchone(
                conn,
                """
                select users.*, auth_sessions.created_at as session_created_at
                from auth_sessions
                join users on users.id = auth_sessions.user_id
                where auth_sessions.token = %s
                """,
                (token,),
                sqlite_query="""
                select users.*, auth_sessions.created_at as session_created_at
                from auth_sessions
                join users on users.id = auth_sessions.user_id
                where auth_sessions.token = ?
                """,
                sqlite_params=(token,),
                dict_row=True,
            )
        if not record:
            return None
        # Enforce session TTL
        session_created_at = record.pop("session_created_at", None)
        if session_created_at:
            created = (
                datetime.fromisoformat(session_created_at)
                if isinstance(session_created_at, str)
                else session_created_at
            )
            if not created.tzinfo:
                created = created.replace(tzinfo=UTC)
            if self._now() > created + timedelta(days=settings.session_ttl_days):
                return None
        record["usage_events"] = self.count_usage_events(record["id"])
        return record

    def update_user_name(self, user_id: str, name: str) -> None:
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                "update users set name = %s where id = %s",
                (name, user_id),
                sqlite_query="update users set name = ? where id = ?",
                sqlite_params=(name, user_id),
            )

    def create_chat_session(self, user_id: str, title: str) -> dict[str, str]:
        record = {
            "id": f"session_{secrets.token_hex(8)}",
            "user_id": user_id,
            "title": title,
            "created_at": self._iso(self._now()),
        }
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                "insert into chat_sessions (id, user_id, title, created_at) values (%(id)s, %(user_id)s, %(title)s, %(created_at)s)",
                record,
                sqlite_query="insert into chat_sessions (id, user_id, title, created_at) values (:id, :user_id, :title, :created_at)",
                sqlite_params=record,
            )
        return record

    def list_chat_sessions(self, user_id: str, limit: int = 50) -> list[dict[str, object]]:
        with self.connect() as conn:
            return self._fetchall(
                conn,
                """
                select id, title, created_at,
                       (select count(*) from chat_messages where session_id = chat_sessions.id) as message_count,
                       (select coalesce(sum(prompt_tokens + completion_tokens), 0)
                        from usage_events where session_id = chat_sessions.id) as tokens_used
                from chat_sessions
                where user_id = %s
                order by created_at desc
                limit %s
                """,
                (user_id, limit),
                sqlite_query="""
                select id, title, created_at,
                       (select count(*) from chat_messages where session_id = chat_sessions.id) as message_count,
                       (select coalesce(sum(prompt_tokens + completion_tokens), 0)
                        from usage_events where session_id = chat_sessions.id) as tokens_used
                from chat_sessions
                where user_id = ?
                order by created_at desc
                limit ?
                """,
                sqlite_params=(user_id, limit),
                dict_rows=True,
            )

    def get_chat_session(self, session_id: str, user_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            return self._fetchone(
                conn,
                "select * from chat_sessions where id = %s and user_id = %s",
                (session_id, user_id),
                sqlite_query="select * from chat_sessions where id = ? and user_id = ?",
                sqlite_params=(session_id, user_id),
                dict_row=True,
            )

    def add_chat_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        record = {
            "id": f"msg_{secrets.token_hex(8)}",
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "created_at": self._iso(self._now()),
        }
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                """
                insert into chat_messages (id, session_id, role, content, metadata, created_at)
                values (%(id)s, %(session_id)s, %(role)s, %(content)s, %(metadata)s::jsonb, %(created_at)s)
                """,
                record,
                sqlite_query="""
                insert into chat_messages (id, session_id, role, content, metadata, created_at)
                values (:id, :session_id, :role, :content, :metadata, :created_at)
                """,
                sqlite_params=record,
            )

    def get_recent_chat_messages(self, session_id: str, limit: int = 12) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = self._fetchall(
                conn,
                """
                select role, content, metadata, created_at
                from chat_messages
                where session_id = %s
                order by created_at desc
                limit %s
                """,
                (session_id, limit),
                sqlite_query="""
                select role, content, metadata, created_at
                from chat_messages
                where session_id = ?
                order by created_at desc
                limit ?
                """,
                sqlite_params=(session_id, limit),
                dict_rows=True,
            )

        return [
            {
                "role": row["role"],
                "content": row["content"],
                "metadata": row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in reversed(rows)
        ]

    def add_usage_event(
        self,
        *,
        user_id: str,
        session_id: str | None,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        record = {
            "id": f"usage_{secrets.token_hex(8)}",
            "user_id": user_id,
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "created_at": self._iso(self._now()),
        }
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                """
                insert into usage_events
                (id, user_id, session_id, provider, model, prompt_tokens, completion_tokens, created_at)
                values (%(id)s, %(user_id)s, %(session_id)s, %(provider)s, %(model)s,
                        %(prompt_tokens)s, %(completion_tokens)s, %(created_at)s)
                """,
                record,
                sqlite_query="""
                insert into usage_events
                (id, user_id, session_id, provider, model, prompt_tokens, completion_tokens, created_at)
                values (:id, :user_id, :session_id, :provider, :model,
                        :prompt_tokens, :completion_tokens, :created_at)
                """,
                sqlite_params=record,
            )

    def get_token_usage_window(self, user_id: str, since: datetime) -> tuple[int, str | None]:
        """
        Return (total_tokens, oldest_event_at) for events in [since, now].

        total_tokens  – sum of prompt_tokens + completion_tokens
        oldest_event_at – ISO timestamp of the earliest event in the window,
                          used to tell the client when the budget will start
                          freeing up (rolling window behaviour).
        """
        with self.connect() as conn:
            row = self._fetchone(
                conn,
                """
                select
                    coalesce(sum(prompt_tokens + completion_tokens), 0) as total,
                    min(created_at) as oldest
                from usage_events
                where user_id = %s and created_at >= %s
                """,
                (user_id, since.isoformat()),
                sqlite_query="""
                select
                    coalesce(sum(prompt_tokens + completion_tokens), 0) as total,
                    min(created_at) as oldest
                from usage_events
                where user_id = ? and created_at >= ?
                """,
                sqlite_params=(user_id, since.isoformat()),
            )
        if not row:
            return 0, None
        total, oldest = row
        oldest_iso = oldest.isoformat() if isinstance(oldest, datetime) else oldest
        return int(total), oldest_iso

    def count_usage_events(self, user_id: str) -> int:
        with self.connect() as conn:
            row = self._fetchone(
                conn,
                "select count(*) from usage_events where user_id = %s",
                (user_id,),
                sqlite_query="select count(*) from usage_events where user_id = ?",
                sqlite_params=(user_id,),
            )
            return int(row[0]) if row else 0

    def get_subscription(self, user_id: str) -> dict[str, str | None]:
        with self.connect() as conn:
            return self._fetchone(
                conn,
                """
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users where id = %s
                """,
                (user_id,),
                sqlite_query="""
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users where id = ?
                """,
                sqlite_params=(user_id,),
                dict_row=True,
            ) or {}

    def get_subscription_by_email(self, email: str) -> dict[str, str | None]:
        with self.connect() as conn:
            return self._fetchone(
                conn,
                """
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users where email = %s
                """,
                (email,),
                sqlite_query="""
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users where email = ?
                """,
                sqlite_params=(email,),
                dict_row=True,
            ) or {}

    def get_user_by_customer_id(self, customer_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            return self._fetchone(
                conn,
                "select * from users where billing_customer_id = %s",
                (customer_id,),
                sqlite_query="select * from users where billing_customer_id = ?",
                sqlite_params=(customer_id,),
                dict_row=True,
            )

    def get_user_by_subscription_id(self, subscription_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            return self._fetchone(
                conn,
                "select * from users where billing_subscription_id = %s",
                (subscription_id,),
                sqlite_query="select * from users where billing_subscription_id = ?",
                sqlite_params=(subscription_id,),
                dict_row=True,
            )

    def set_billing_customer(self, user_id: str, customer_id: str) -> None:
        with self._lock, self.connect() as conn:
            self._execute(
                conn,
                "update users set billing_customer_id = %s where id = %s",
                (customer_id, user_id),
                sqlite_query="update users set billing_customer_id = ? where id = ?",
                sqlite_params=(customer_id, user_id),
            )

    def update_subscription_state(
        self,
        *,
        user_id: str | None = None,
        email: str | None = None,
        status_value: str,
        customer_id: str | None = None,
        subscription_id: str | None = None,
    ) -> dict[str, str]:
        if not user_id and not email:
            raise ValueError("user_id or email is required")

        with self._lock, self.connect() as conn:
            if user_id:
                self._execute(
                    conn,
                    """
                    update users
                    set subscription_status = %s,
                        billing_customer_id = coalesce(%s, billing_customer_id),
                        billing_subscription_id = coalesce(%s, billing_subscription_id)
                    where id = %s
                    """,
                    (status_value, customer_id, subscription_id, user_id),
                    sqlite_query="""
                    update users
                    set subscription_status = ?,
                        billing_customer_id = coalesce(?, billing_customer_id),
                        billing_subscription_id = coalesce(?, billing_subscription_id)
                    where id = ?
                    """,
                    sqlite_params=(status_value, customer_id, subscription_id, user_id),
                )
                row = self._fetchone(
                    conn,
                    "select * from users where id = %s",
                    (user_id,),
                    sqlite_query="select * from users where id = ?",
                    sqlite_params=(user_id,),
                    dict_row=True,
                )
            else:
                self._execute(
                    conn,
                    """
                    update users
                    set subscription_status = %s,
                        billing_customer_id = coalesce(%s, billing_customer_id),
                        billing_subscription_id = coalesce(%s, billing_subscription_id)
                    where email = %s
                    """,
                    (status_value, customer_id, subscription_id, email),
                    sqlite_query="""
                    update users
                    set subscription_status = ?,
                        billing_customer_id = coalesce(?, billing_customer_id),
                        billing_subscription_id = coalesce(?, billing_subscription_id)
                    where email = ?
                    """,
                    sqlite_params=(status_value, customer_id, subscription_id, email),
                )
                row = self._fetchone(
                    conn,
                    "select * from users where email = %s",
                    (email,),
                    sqlite_query="select * from users where email = ?",
                    sqlite_params=(email,),
                    dict_row=True,
                )
            if row is None:
                raise ValueError("user not found")
            return row

    def require_active_access(self, user: dict[str, str]) -> None:
        now = self._now()
        status_value = user["subscription_status"]
        trial_ends_at = user["trial_ends_at"]
        if isinstance(trial_ends_at, str):
            trial_ends_at = datetime.fromisoformat(trial_ends_at)

        if status_value == "active":
            return
        if status_value == "trialing" and trial_ends_at > now:
            return

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription is required to continue using Krud AI",
        )

    def _generate_user_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return f"{''.join(secrets.choice(alphabet) for _ in range(4))}-{''.join(secrets.choice(alphabet) for _ in range(4))}"
