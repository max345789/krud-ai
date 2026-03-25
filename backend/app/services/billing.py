"""
Billing service — Dodo Payments integration.

Replaces the previous Stripe implementation.

Modes
─────
  mock  – HTML form billing for local development and demos.
           No API keys required; subscription state is toggled via a simple form.
  dodo  – Real recurring payments via Dodo Payments (dodopayments Python SDK).
           Requires DODO_PAYMENTS_API_KEY, DODO_PAYMENTS_WEBHOOK_KEY, and
           DODO_PAYMENTS_PRODUCT_ID to be set.

Checkout flow
─────────────
  1. create_checkout()   → returns a Dodo checkout URL; user pays there
  2. Dodo fires          → subscription.active webhook → handle_webhook()
  3. handle_webhook()    → looks up user by metadata.user_id (preferred) or
                           billing_customer_id (fallback), sets status = active

Portal flow
───────────
  1. create_portal()     → returns a Dodo customer-portal URL
  2. User self-serves    → Dodo fires subscription.updated / .cancelled webhook
  3. handle_webhook()    → updates subscription status in DB

Webhook event mapping
─────────────────────
  subscription.active    → active
  subscription.renewed   → active
  subscription.updated   → mirror Dodo status field
  subscription.on_hold   → past_due
  subscription.failed    → past_due
  subscription.cancelled → canceled
  subscription.expired   → canceled
  (all others)           → acknowledged, no DB change
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from app.core.config import settings
from app.core.db import Database

# Lazy import: the dodopayments package may not be installed in dev environments
# that only run in mock mode.  We guard the import so the app still starts.
try:
    from dodopayments import DodoPayments as _DodoClient
    _DODO_AVAILABLE = True
except ImportError:
    _DodoClient = None  # type: ignore[assignment, misc]
    _DODO_AVAILABLE = False


@dataclass
class BillingSession:
    url: str
    mode: Literal["mock", "dodo"]


def _map_dodo_status(raw: str | None) -> str:
    """
    Translate a Dodo subscription status string to our four internal states.

    Dodo statuses not explicitly listed here fall through to "canceled" as the
    safest default — better to require re-subscription than to grant free access.
    """
    if raw in {"active"}:
        return "active"
    if raw in {"trialing"}:
        return "trialing"
    if raw in {"on_hold", "failed", "overdue", "incomplete"}:
        return "past_due"
    if raw in {"cancelled", "canceled", "expired"}:
        return "canceled"
    return "canceled"


class BillingService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self._client: _DodoClient | None = None  # type: ignore[valid-type]

        if _DODO_AVAILABLE and settings.dodo_api_key:
            self._client = _DodoClient(
                bearer_token=settings.dodo_api_key,
                environment=settings.dodo_environment,  # "test_mode" or "live_mode"
            )

    # ── internal helpers ───────────────────────────────────────────────────

    @property
    def _is_mock(self) -> bool:
        """True when no real Dodo client is configured or mode is explicitly mock."""
        return settings.billing_mode == "mock" or self._client is None

    def _require_client(self):
        """Raise clearly if Dodo is requested but SDK/key is missing."""
        if self._client is None:
            raise ValueError(
                "DODO_PAYMENTS_API_KEY is not set or the dodopayments package is "
                "not installed. Set KRUD_BILLING_MODE=mock for local development."
            )
        return self._client

    # ── public API ─────────────────────────────────────────────────────────

    @property
    def checkout_enabled(self) -> bool:
        return self._is_mock or bool(settings.dodo_product_id)

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
                # price_id field repurposed to carry the Dodo product ID
                "price_id": settings.dodo_product_id,
                "customer_id": subscription.get("billing_customer_id"),
                "subscription_id": subscription.get("billing_subscription_id"),
            },
            "usage_events": self.db.count_usage_events(user["id"]),
        }

    def create_checkout(self, user: dict) -> BillingSession:
        """
        Start a Dodo Payments checkout session.

        The user's ID is embedded in the product metadata so that the
        subscription.active webhook can resolve back to the correct DB row
        without a secondary email lookup.
        """
        if self._is_mock:
            return BillingSession(
                url=(
                    f"{settings.public_base_url}/billing/mock-checkout"
                    f"?email={user['email']}&plan={settings.dodo_product_id}"
                ),
                mode="mock",
            )

        client = self._require_client()

        session = client.checkout_sessions.create(
            product_cart=[{"product_id": settings.dodo_product_id, "quantity": 1}],
            customer={"email": user["email"], "name": user.get("name") or ""},
            return_url=settings.billing_success_url,
            # metadata is attached to the subscription created by Dodo so that
            # webhooks can carry user_id back to us without a reverse-lookup.
            metadata={"user_id": user["id"]},
        )

        # Dodo may return a customer_id on the session object; store it early
        # so portal creation works even before the first webhook fires.
        customer_id = getattr(session, "customer_id", None)
        if customer_id:
            self.db.set_billing_customer(user["id"], str(customer_id))

        return BillingSession(url=str(session.checkout_url), mode="dodo")

    def create_portal(self, user: dict) -> BillingSession:
        """
        Open a Dodo customer-portal session so the user can manage their subscription.

        Requires billing_customer_id to be stored (populated either at checkout
        time or by the first incoming webhook).
        """
        if self._is_mock:
            return BillingSession(
                url=f"{settings.public_base_url}/billing/mock-portal?email={user['email']}",
                mode="mock",
            )

        client = self._require_client()
        subscription = self.db.get_subscription(user["id"])
        customer_id = subscription.get("billing_customer_id")
        if not customer_id:
            raise ValueError("No billing customer is attached to this account yet")

        portal = client.customers.customer_portal.create(customer_id=customer_id)
        return BillingSession(url=str(portal.link), mode="dodo")

    def handle_webhook(
        self,
        payload: bytes,
        webhook_headers: dict[str, str],
    ) -> dict[str, str]:
        """
        Verify and process an inbound webhook.

        In mock mode the raw JSON body is trusted directly (no signature check).
        In dodo mode the SDK verifies the HMAC-SHA256 signature using the three
        Dodo webhook headers before any payload data is read.
        """
        if self._is_mock:
            return self._handle_mock_webhook(payload)

        if not settings.dodo_webhook_key:
            raise ValueError("DODO_PAYMENTS_WEBHOOK_KEY is not configured")

        client = self._require_client()
        try:
            event = client.webhooks.unwrap(payload, headers=webhook_headers)
        except Exception as exc:
            # Do not surface the low-level exception message — it might leak
            # implementation details.  The caller raises a sanitised 400.
            raise ValueError("Webhook signature verification failed") from exc

        return self._process_dodo_event(event)

    # ── private helpers ────────────────────────────────────────────────────

    def _handle_mock_webhook(self, payload: bytes) -> dict[str, str]:
        """Parse and apply a mock webhook body (no signature required)."""
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Mock webhook payload is not valid JSON") from exc

        email = data.get("email", "")
        if not isinstance(email, str) or not email.strip():
            raise ValueError("Mock webhook must include a non-empty 'email' field")

        # Circular import avoided by importing here rather than at module level.
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

    def _process_dodo_event(self, event: object) -> dict[str, str]:
        """
        Map a verified Dodo webhook event to a DB subscription state change.

        Resolution order for the affected user:
          1. metadata.user_id  — set at checkout creation time (preferred)
          2. billing_customer_id — fallback via DB lookup by Dodo customer_id
        """
        event_type: str = getattr(event, "type", "") or ""
        data = getattr(event, "data", None)

        if data is None:
            return {"status": "skipped"}

        customer_id: str = str(getattr(data, "customer_id", "") or "")
        subscription_id: str = str(getattr(data, "subscription_id", "") or "")
        metadata: dict = getattr(data, "metadata", {}) or {}
        user_id: str | None = metadata.get("user_id") if isinstance(metadata, dict) else None

        # Determine target status from event type.
        if event_type == "subscription.active":
            status_value = "active"
        elif event_type == "subscription.renewed":
            status_value = "active"
        elif event_type == "subscription.updated":
            raw = str(getattr(data, "status", "") or "")
            status_value = _map_dodo_status(raw)
        elif event_type in {"subscription.on_hold", "subscription.failed"}:
            status_value = "past_due"
        elif event_type in {"subscription.cancelled", "subscription.expired"}:
            status_value = "canceled"
        else:
            # Unknown or uninteresting event — acknowledge without DB write.
            return {"status": "skipped"}

        # Resolve user: prefer metadata.user_id, fall back to customer_id lookup.
        if not user_id and customer_id:
            found = self.db.get_user_by_customer_id(customer_id)
            if found:
                user_id = found["id"]

        if not user_id:
            # Cannot resolve user — skip silently so Dodo gets a 200 and stops
            # retrying; the event may arrive out of order before checkout completes.
            return {"status": "skipped"}

        self.db.update_subscription_state(
            user_id=user_id,
            status_value=status_value,
            customer_id=customer_id or None,
            subscription_id=subscription_id or None,
        )
        return {"status": status_value}
