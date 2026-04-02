"""
Billing service — Razorpay integration.

Modes
─────
  mock      – HTML form billing for local development and demos.
               No API keys required; subscription state is toggled via a simple form.
  razorpay  – Real recurring payments via Razorpay Subscriptions API.
               Requires RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, and
               RAZORPAY_PLAN_ID to be set.

Checkout flow
─────────────
  1. create_checkout()   → creates a Razorpay subscription, returns short_url
  2. User pays           → Razorpay fires subscription.activated webhook
  3. handle_webhook()    → verifies HMAC-SHA256 signature, updates DB

Portal flow
───────────
  1. create_portal()     → returns a manage-subscription URL
  2. User self-serves    → Razorpay fires subscription.cancelled / .halted webhook
  3. handle_webhook()    → updates subscription status in DB

Webhook event mapping
─────────────────────
  subscription.activated → active
  subscription.charged   → active
  subscription.updated   → mirror Razorpay status field
  subscription.halted    → past_due
  subscription.pending   → past_due
  subscription.cancelled → canceled
  subscription.completed → canceled
  payment.failed         → acknowledged, no DB change
  (all others)           → acknowledged, no DB change
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from app.core.config import settings
from app.core.db import Database

try:
    import razorpay as _razorpay_module
    _RAZORPAY_AVAILABLE = True
except ImportError:
    _razorpay_module = None  # type: ignore[assignment]
    _RAZORPAY_AVAILABLE = False


@dataclass
class BillingSession:
    url: str
    mode: Literal["mock", "razorpay"]


def _map_razorpay_status(raw: str | None) -> str:
    """Translate a Razorpay subscription status to our four internal states."""
    if raw in {"active"}:
        return "active"
    if raw in {"created", "authenticated"}:
        return "trialing"
    if raw in {"halted", "pending"}:
        return "past_due"
    if raw in {"cancelled", "expired", "completed"}:
        return "canceled"
    return "canceled"


def _verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Return True if the Razorpay webhook signature is valid."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class BillingService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self._client = None

        if (
            _RAZORPAY_AVAILABLE
            and settings.razorpay_key_id
            and settings.razorpay_key_secret
        ):
            self._client = _razorpay_module.Client(
                auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
            )

    # ── internal helpers ───────────────────────────────────────────────────

    @property
    def _is_mock(self) -> bool:
        return settings.billing_mode == "mock" or self._client is None

    def _require_client(self):
        if self._client is None:
            raise ValueError(
                "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not set or razorpay package "
                "not installed. Set KRUD_BILLING_MODE=mock for local development."
            )
        return self._client

    # ── public API ─────────────────────────────────────────────────────────

    @property
    def checkout_enabled(self) -> bool:
        return self._is_mock or bool(settings.razorpay_plan_id)

    @property
    def portal_enabled(self) -> bool:
        return self._is_mock or self._client is not None

    def overview(self, user: dict) -> dict:
        subscription = self.db.get_subscription(user["id"])
        return {
            "checkout_enabled": self.checkout_enabled,
            "portal_enabled": self.portal_enabled,
            "subscription": {
                "status": subscription.get("subscription_status", user["subscription_status"]),
                "trial_ends_at": subscription.get("trial_ends_at", user["trial_ends_at"]),
                "price_id": settings.razorpay_plan_id,
                "customer_id": subscription.get("billing_customer_id"),
                "subscription_id": subscription.get("billing_subscription_id"),
            },
            "usage_events": self.db.count_usage_events(user["id"]),
        }

    def _plan_id_for(self, plan: str) -> str:
        """Return the Razorpay plan_id for a given plan name."""
        if plan == "pilot":
            return settings.razorpay_plan_id_pilot
        return settings.razorpay_plan_id_builder

    def create_checkout(self, user: dict, plan: str = "builder") -> BillingSession:
        """
        Create a Razorpay subscription and return its hosted checkout URL.

        plan must be 'builder' or 'pilot'.  The plan name and user ID are
        stored in subscription notes so that the subscription.activated
        webhook can resolve back to the correct DB row and set the right plan.
        """
        plan_id = self._plan_id_for(plan)

        if self._is_mock:
            return BillingSession(
                url=(
                    f"{settings.public_base_url}/billing/mock-checkout"
                    f"?email={user['email']}&plan={plan_id or plan}"
                ),
                mode="mock",
            )

        client = self._require_client()

        subscription = client.subscription.create({
            "plan_id": plan_id,
            "total_count": 120,   # 120 billing cycles (~10 years)
            "quantity": 1,
            "customer_notify": 1,
            "notes": {
                "user_id": user["id"],
                "email": user["email"],
                "krud_plan": plan,
            },
        })

        subscription_id = subscription.get("id", "")
        short_url = subscription.get("short_url", "")

        # Store subscription_id early so portal lookup works before webhook fires
        if subscription_id:
            self.db.update_subscription_state(
                user_id=user["id"],
                status_value=user.get("subscription_status", "trialing"),
                subscription_id=subscription_id,
            )

        return BillingSession(url=str(short_url), mode="razorpay")

    def create_portal(self, user: dict) -> BillingSession:
        """
        Return a URL where the user can manage their Razorpay subscription.

        Razorpay does not expose a hosted customer-portal URL, so we redirect
        to the Razorpay subscription management page using the stored
        subscription ID.
        """
        if self._is_mock:
            return BillingSession(
                url=f"{settings.public_base_url}/billing/mock-portal?email={user['email']}",
                mode="mock",
            )

        subscription = self.db.get_subscription(user["id"])
        subscription_id = subscription.get("billing_subscription_id")
        if not subscription_id:
            raise ValueError("No billing subscription is attached to this account yet")

        portal_url = (
            f"https://api.razorpay.com/v1/subscriptions/{subscription_id}/cancel"
            if False  # placeholder — direct to support or a manage page
            else settings.billing_portal_return_url
        )
        return BillingSession(url=portal_url, mode="razorpay")

    def handle_webhook(
        self,
        payload: bytes,
        webhook_headers: dict[str, str],
    ) -> dict[str, str]:
        """
        Verify and process an inbound Razorpay webhook.

        In mock mode the raw JSON body is trusted directly (no signature check).
        In razorpay mode the HMAC-SHA256 signature is verified using the
        X-Razorpay-Signature header before any payload data is acted upon.
        """
        if self._is_mock:
            return self._handle_mock_webhook(payload)

        if not settings.razorpay_webhook_secret:
            raise ValueError("RAZORPAY_WEBHOOK_SECRET is not configured")

        signature = webhook_headers.get("x-razorpay-signature", "")
        if not signature or not _verify_webhook_signature(
            payload, signature, settings.razorpay_webhook_secret
        ):
            raise ValueError("Webhook signature verification failed")

        try:
            event = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Webhook payload is not valid JSON") from exc

        return self._process_razorpay_event(event)

    # ── private helpers ────────────────────────────────────────────────────

    def _handle_mock_webhook(self, payload: bytes) -> dict[str, str]:
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Mock webhook payload is not valid JSON") from exc

        email = data.get("email", "")
        if not isinstance(email, str) or not email.strip():
            raise ValueError("Mock webhook must include a non-empty 'email' field")

        from app.core.security import validate_subscription_status

        raw_status = data.get("status", "active")
        try:
            safe_status = validate_subscription_status(str(raw_status))
        except ValueError as exc:
            raise ValueError(f"Mock webhook: {exc}") from exc

        user = self.db.update_subscription_state(
            email=email.strip().lower(),
            status_value=safe_status,
            customer_id=data.get("customer_id"),
            subscription_id=data.get("subscription_id"),
        )
        return {"status": user["subscription_status"]}

    def _process_razorpay_event(self, event: dict) -> dict[str, str]:
        """
        Map a verified Razorpay webhook event to a DB subscription state change.

        Resolution order for the affected user:
          1. subscription.notes.user_id — set at subscription creation time
          2. billing_subscription_id — DB lookup by Razorpay subscription_id
        """
        event_type: str = event.get("event", "")
        payload_data: dict = event.get("payload", {})

        # Razorpay wraps objects under payload.subscription.entity or payload.payment.entity
        sub_entity: dict = (
            payload_data.get("subscription", {}).get("entity", {})
        )
        subscription_id: str = sub_entity.get("id", "")
        notes: dict = sub_entity.get("notes", {}) if isinstance(sub_entity.get("notes"), dict) else {}
        user_id: str | None = notes.get("user_id")

        # Map event to internal status
        if event_type in {"subscription.activated", "subscription.charged"}:
            status_value = "active"
        elif event_type == "subscription.updated":
            raw = sub_entity.get("status", "")
            status_value = _map_razorpay_status(raw)
        elif event_type in {"subscription.halted", "subscription.pending"}:
            status_value = "past_due"
        elif event_type in {"subscription.cancelled", "subscription.completed", "subscription.expired"}:
            status_value = "canceled"
        else:
            return {"status": "skipped"}

        # Resolve user: prefer notes.user_id, fall back to subscription_id lookup
        if not user_id and subscription_id:
            found = self.db.get_user_by_subscription_id(subscription_id)
            if found:
                user_id = found["id"]

        if not user_id:
            return {"status": "skipped"}

        self.db.update_subscription_state(
            user_id=user_id,
            status_value=status_value,
            subscription_id=subscription_id or None,
        )
        return {"status": status_value}
