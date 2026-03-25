from __future__ import annotations

import json
import secrets
import sqlite3
import string
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.schemas import DeviceApprovalRequest


class Database:
    _lock = Lock()

    def __init__(self) -> None:
        self.path = Path(settings.database_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                create table if not exists device_codes (
                    device_code text primary key,
                    user_code text unique not null,
                    client_name text not null,
                    status text not null,
                    email text,
                    name text,
                    session_token text,
                    user_id text,
                    created_at text not null,
                    expires_at text not null
                );

                create table if not exists users (
                    id text primary key,
                    email text unique not null,
                    name text,
                    subscription_status text not null,
                    trial_ends_at text not null,
                    billing_customer_id text,
                    billing_subscription_id text,
                    created_at text not null
                );

                create table if not exists auth_sessions (
                    token text primary key,
                    user_id text not null,
                    created_at text not null
                );

                create table if not exists chat_sessions (
                    id text primary key,
                    user_id text not null,
                    title text not null,
                    created_at text not null
                );

                create table if not exists chat_messages (
                    id text primary key,
                    session_id text not null,
                    role text not null,
                    content text not null,
                    metadata text,
                    created_at text not null
                );

                create table if not exists usage_events (
                    id text primary key,
                    user_id text not null,
                    session_id text,
                    provider text not null,
                    model text not null,
                    prompt_tokens integer not null default 0,
                    completion_tokens integer not null default 0,
                    created_at text not null
                );
                """
            )
            self._ensure_column(conn, "users", "billing_customer_id", "text")
            self._ensure_column(conn, "users", "billing_subscription_id", "text")
            self._ensure_column(conn, "chat_messages", "metadata", "text")
            conn.commit()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in conn.execute(f"pragma table_info({table})")}
        if column not in columns:
            conn.execute(f"alter table {table} add column {column} {definition}")

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _iso(self, value: datetime) -> str:
        return value.isoformat()

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
            conn.execute(
                """
                insert into device_codes (device_code, user_code, client_name, status, created_at, expires_at)
                values (:device_code, :user_code, :client_name, :status, :created_at, :expires_at)
                """,
                record,
            )
            conn.commit()
        return record

    def complete_device_code(self, user_code: str, approval: DeviceApprovalRequest) -> dict[str, str]:
        now = self._now()
        with self._lock, self.connect() as conn:
            record = conn.execute(
                "select * from device_codes where user_code = ?",
                (user_code,),
            ).fetchone()
            if record is None:
                raise ValueError("Unknown user code")
            if datetime.fromisoformat(record["expires_at"]) <= now:
                conn.execute("update device_codes set status = 'expired' where user_code = ?", (user_code,))
                conn.commit()
                raise ValueError("Device code has expired")

            user = conn.execute("select * from users where email = ?", (approval.email.lower(),)).fetchone()
            if user is None:
                user_id = f"user_{secrets.token_hex(8)}"
                trial_ends_at = self._iso(now + timedelta(days=settings.trial_days))
                conn.execute(
                    """
                    insert into users (
                        id, email, name, subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id, created_at
                    )
                    values (?, ?, ?, 'trialing', ?, null, null, ?)
                    """,
                    (user_id, approval.email.lower(), approval.name, trial_ends_at, self._iso(now)),
                )
                subscription_status = "trialing"
                name = approval.name
            else:
                user_id = user["id"]
                subscription_status = user["subscription_status"]
                trial_ends_at = user["trial_ends_at"]
                name = user["name"]

            session_token = f"krud_{secrets.token_urlsafe(24)}"
            conn.execute(
                "insert into auth_sessions (token, user_id, created_at) values (?, ?, ?)",
                (session_token, user_id, self._iso(now)),
            )
            conn.execute(
                """
                update device_codes
                set status = 'approved', email = ?, name = ?, session_token = ?, user_id = ?
                where user_code = ?
                """,
                (approval.email.lower(), approval.name or name, session_token, user_id, user_code),
            )
            conn.commit()
        return {
            "status": "approved",
            "session_token": session_token,
            "user_id": user_id,
            "subscription_status": subscription_status,
            "trial_ends_at": trial_ends_at,
        }

    def poll_device_code(self, device_code: str) -> dict[str, str | None]:
        now = self._now()
        with self.connect() as conn:
            record = conn.execute(
                "select * from device_codes where device_code = ?",
                (device_code,),
            ).fetchone()
            if record is None:
                return {"status": "expired"}
            if datetime.fromisoformat(record["expires_at"]) <= now:
                return {"status": "expired"}
            if record["status"] != "approved":
                return {"status": "pending"}
            user = conn.execute("select * from users where id = ?", (record["user_id"],)).fetchone()
            return {
                "status": "approved",
                "session_token": record["session_token"],
                "user_id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "subscription_status": user["subscription_status"],
                "trial_ends_at": user["trial_ends_at"],
                "billing_customer_id": user["billing_customer_id"],
                "billing_subscription_id": user["billing_subscription_id"],
            }

    def get_user_by_session_token(self, token: str) -> dict[str, str] | None:
        with self.connect() as conn:
            record = conn.execute(
                """
                select users.*
                from auth_sessions
                join users on users.id = auth_sessions.user_id
                where auth_sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if not record:
                return None
            payload = dict(record)
            payload["usage_events"] = self.count_usage_events(payload["id"])
            return payload

    def create_chat_session(self, user_id: str, title: str) -> dict[str, str]:
        record = {
            "id": f"session_{secrets.token_hex(8)}",
            "user_id": user_id,
            "title": title,
            "created_at": self._iso(self._now()),
        }
        with self._lock, self.connect() as conn:
            conn.execute(
                "insert into chat_sessions (id, user_id, title, created_at) values (:id, :user_id, :title, :created_at)",
                record,
            )
            conn.commit()
        return record

    def get_chat_session(self, session_id: str, user_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            record = conn.execute(
                "select * from chat_sessions where id = ? and user_id = ?",
                (session_id, user_id),
            ).fetchone()
            return dict(record) if record else None

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
            conn.execute(
                """
                insert into chat_messages (id, session_id, role, content, metadata, created_at)
                values (:id, :session_id, :role, :content, :metadata, :created_at)
                """,
                record,
            )
            conn.commit()

    def get_recent_chat_messages(self, session_id: str, limit: int = 12) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select role, content, metadata, created_at
                from chat_messages
                where session_id = ?
                order by created_at desc
                limit ?
                """,
                (session_id, limit),
            ).fetchall()

        return [
            {
                "role": row["role"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"] or "{}"),
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
            conn.execute(
                """
                insert into usage_events
                (id, user_id, session_id, provider, model, prompt_tokens, completion_tokens, created_at)
                values (:id, :user_id, :session_id, :provider, :model, :prompt_tokens, :completion_tokens, :created_at)
                """,
                record,
            )
            conn.commit()

    def count_usage_events(self, user_id: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "select count(*) as count from usage_events where user_id = ?",
                (user_id,),
            ).fetchone()
            return int(row["count"]) if row else 0

    def get_subscription(self, user_id: str) -> dict[str, str | None]:
        with self.connect() as conn:
            row = conn.execute(
                """
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users
                where id = ?
                """,
                (user_id,),
            ).fetchone()
            return dict(row) if row else {}

    def get_subscription_by_email(self, email: str) -> dict[str, str | None]:
        with self.connect() as conn:
            row = conn.execute(
                """
                select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                from users
                where email = ?
                """,
                (email,),
            ).fetchone()
            return dict(row) if row else {}

    def set_billing_customer(self, user_id: str, customer_id: str) -> None:
        with self._lock, self.connect() as conn:
            conn.execute(
                "update users set billing_customer_id = ? where id = ?",
                (customer_id, user_id),
            )
            conn.commit()

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

        predicate = "id = ?" if user_id else "email = ?"
        lookup = user_id or email
        with self._lock, self.connect() as conn:
            conn.execute(
                f"""
                update users
                set subscription_status = ?,
                    billing_customer_id = coalesce(?, billing_customer_id),
                    billing_subscription_id = coalesce(?, billing_subscription_id)
                where {predicate}
                """,
                (status_value, customer_id, subscription_id, lookup),
            )
            conn.commit()
            row = conn.execute(f"select * from users where {predicate}", (lookup,)).fetchone()
            if row is None:
                raise ValueError("user not found")
            return dict(row)

    def require_active_access(self, user: dict[str, str]) -> None:
        now = self._now()
        status_value = user["subscription_status"]
        trial_ends_at = datetime.fromisoformat(user["trial_ends_at"])

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
