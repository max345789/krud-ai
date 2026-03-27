from __future__ import annotations

import json
import secrets
import string
from datetime import UTC, datetime, timedelta
from threading import Lock

import psycopg2
import psycopg2.extras
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.schemas import DeviceApprovalRequest


class Database:
    _lock = Lock()

    def connect(self) -> psycopg2.extensions.connection:
        url = settings.database_url
        # Supabase requires SSL; append sslmode if not already in the URL
        if url and "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        conn = psycopg2.connect(url)
        psycopg2.extras.register_default_jsonb(conn)
        return conn

    def _row(self, row) -> dict | None:
        """Convert a RealDictRow to a plain dict, serialising datetime → ISO string."""
        if row is None:
            return None
        result = {}
        for k, v in dict(row).items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

    def initialize(self) -> None:
        # Schema is managed via Supabase migrations — nothing to do at startup.
        pass

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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into device_codes (device_code, user_code, client_name, status, created_at, expires_at)
                    values (%(device_code)s, %(user_code)s, %(client_name)s, %(status)s, %(created_at)s, %(expires_at)s)
                    """,
                    record,
                )
        return record

    def complete_device_code(self, user_code: str, approval: DeviceApprovalRequest) -> dict[str, str]:
        now = self._now()
        with self._lock, self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "select * from device_codes where user_code = %s",
                    (user_code,),
                )
                record = self._row(cur.fetchone())
            if record is None:
                raise ValueError("Unknown user code")

            expires_at = record["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at <= now:
                with conn.cursor() as cur:
                    cur.execute(
                        "update device_codes set status = 'expired' where user_code = %s",
                        (user_code,),
                    )
                raise ValueError("Device code has expired")

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "select * from users where email = %s",
                    (approval.email.lower(),),
                )
                user = self._row(cur.fetchone())

            if user is None:
                user_id = f"user_{secrets.token_hex(8)}"
                trial_ends_at = self._iso(now + timedelta(days=settings.trial_days))
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into users (id, email, name, subscription_status, trial_ends_at,
                            billing_customer_id, billing_subscription_id, created_at)
                        values (%s, %s, %s, 'trialing', %s, null, null, %s)
                        """,
                        (user_id, approval.email.lower(), approval.name, trial_ends_at, self._iso(now)),
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
            with conn.cursor() as cur:
                cur.execute(
                    "insert into auth_sessions (token, user_id, created_at) values (%s, %s, %s)",
                    (session_token, user_id, self._iso(now)),
                )
                cur.execute(
                    """
                    update device_codes
                    set status = 'approved', email = %s, name = %s, session_token = %s, user_id = %s
                    where user_code = %s
                    """,
                    (approval.email.lower(), approval.name or name, session_token, user_id, user_code),
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "select * from device_codes where device_code = %s",
                    (device_code,),
                )
                record = self._row(cur.fetchone())
            if record is None:
                return {"status": "expired"}

            expires_at = record["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at <= now:
                return {"status": "expired"}
            if record["status"] != "approved":
                return {"status": "pending"}

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("select * from users where id = %s", (record["user_id"],))
                user = self._row(cur.fetchone())

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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    select users.*, auth_sessions.created_at as session_created_at
                    from auth_sessions
                    join users on users.id = auth_sessions.user_id
                    where auth_sessions.token = %s
                    """,
                    (token,),
                )
                record = self._row(cur.fetchone())
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
                return None  # expired — caller will return 401
        record["usage_events"] = self.count_usage_events(record["id"])
        return record

    def update_user_name(self, user_id: str, name: str) -> None:
        with self._lock, self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "update users set name = %s where id = %s",
                    (name, user_id),
                )

    def create_chat_session(self, user_id: str, title: str) -> dict[str, str]:
        record = {
            "id": f"session_{secrets.token_hex(8)}",
            "user_id": user_id,
            "title": title,
            "created_at": self._iso(self._now()),
        }
        with self._lock, self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "insert into chat_sessions (id, user_id, title, created_at) values (%(id)s, %(user_id)s, %(title)s, %(created_at)s)",
                    record,
                )
        return record

    def list_chat_sessions(self, user_id: str, limit: int = 50) -> list[dict[str, object]]:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
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
                )
                return [self._row(r) for r in cur.fetchall()]

    def get_chat_session(self, session_id: str, user_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "select * from chat_sessions where id = %s and user_id = %s",
                    (session_id, user_id),
                )
                return self._row(cur.fetchone())

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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into chat_messages (id, session_id, role, content, metadata, created_at)
                    values (%(id)s, %(session_id)s, %(role)s, %(content)s, %(metadata)s::jsonb, %(created_at)s)
                    """,
                    record,
                )

    def get_recent_chat_messages(self, session_id: str, limit: int = 12) -> list[dict[str, object]]:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    select role, content, metadata, created_at
                    from chat_messages
                    where session_id = %s
                    order by created_at desc
                    limit %s
                    """,
                    (session_id, limit),
                )
                rows = [self._row(r) for r in cur.fetchall()]

        return [
            {
                "role": row["role"],
                "content": row["content"],
                # metadata is jsonb — psycopg2 returns a dict directly
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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into usage_events
                    (id, user_id, session_id, provider, model, prompt_tokens, completion_tokens, created_at)
                    values (%(id)s, %(user_id)s, %(session_id)s, %(provider)s, %(model)s,
                            %(prompt_tokens)s, %(completion_tokens)s, %(created_at)s)
                    """,
                    record,
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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        coalesce(sum(prompt_tokens + completion_tokens), 0) as total,
                        min(created_at) as oldest
                    from usage_events
                    where user_id = %s and created_at >= %s
                    """,
                    (user_id, since.isoformat()),
                )
                row = cur.fetchone()
        if not row:
            return 0, None
        total, oldest = row
        oldest_iso = oldest.isoformat() if isinstance(oldest, datetime) else oldest
        return int(total), oldest_iso

    def count_usage_events(self, user_id: str) -> int:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select count(*) from usage_events where user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0

    def get_subscription(self, user_id: str) -> dict[str, str | None]:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                    from users where id = %s
                    """,
                    (user_id,),
                )
                return self._row(cur.fetchone()) or {}

    def get_subscription_by_email(self, email: str) -> dict[str, str | None]:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    select subscription_status, trial_ends_at, billing_customer_id, billing_subscription_id
                    from users where email = %s
                    """,
                    (email,),
                )
                return self._row(cur.fetchone()) or {}

    def get_user_by_customer_id(self, customer_id: str) -> dict[str, str] | None:
        with self.connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "select * from users where billing_customer_id = %s",
                    (customer_id,),
                )
                return self._row(cur.fetchone())

    def set_billing_customer(self, user_id: str, customer_id: str) -> None:
        with self._lock, self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "update users set billing_customer_id = %s where id = %s",
                    (customer_id, user_id),
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if user_id:
                    cur.execute(
                        """
                        update users
                        set subscription_status = %s,
                            billing_customer_id = coalesce(%s, billing_customer_id),
                            billing_subscription_id = coalesce(%s, billing_subscription_id)
                        where id = %s
                        """,
                        (status_value, customer_id, subscription_id, user_id),
                    )
                    cur.execute("select * from users where id = %s", (user_id,))
                else:
                    cur.execute(
                        """
                        update users
                        set subscription_status = %s,
                            billing_customer_id = coalesce(%s, billing_customer_id),
                            billing_subscription_id = coalesce(%s, billing_subscription_id)
                        where email = %s
                        """,
                        (status_value, customer_id, subscription_id, email),
                    )
                    cur.execute("select * from users where email = %s", (email,))
                row = self._row(cur.fetchone())
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
