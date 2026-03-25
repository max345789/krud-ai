from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

import stripe

from app.core.config import settings
from app.core.db import Database


@dataclass
class BillingSession:
    url: str
    mode: Literal["mock", "stripe"]


class BillingService:
    def __init__(self, db: Database) -> None:
        self.db = db
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    @property
    def checkout_enabled(self) -> bool:
        return settings.billing_mode == "mock" or bool(settings.stripe_secret_key and settings.stripe_price_id)

    @property
    def portal_enabled(self) -> bool:
        return settings.billing_mode == "mock" or bool(settings.stripe_secret_key)

    def overview(self, user: dict[str, str]) -> dict[str, object]:
        subscription = self.db.get_subscription(user["id"])
        return {
            "checkout_enabled": self.checkout_enabled,
            "portal_enabled": self.portal_enabled,
            "subscription": {
                "status": subscription.get("subscription_status", user["subscription_status"]),
                "trial_ends_at": subscription.get("trial_ends_at", user["trial_ends_at"]),
                "price_id": settings.stripe_price_id,
                "customer_id": subscription.get("billing_customer_id"),
                "subscription_id": subscription.get("billing_subscription_id"),
            },
            "usage_events": self.db.count_usage_events(user["id"]),
        }

    def create_checkout(self, user: dict[str, str]) -> BillingSession:
        if settings.billing_mode == "mock" or not settings.stripe_secret_key:
            return BillingSession(
                url=f"{settings.public_base_url}/billing/mock-checkout?email={user['email']}&plan={settings.stripe_price_id}",
                mode="mock",
            )

        session = stripe.checkout.Session.create(
            mode="subscription",
            success_url=settings.billing_success_url,
            cancel_url=settings.billing_cancel_url,
            line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
            customer_email=user["email"],
            metadata={"user_id": user["id"]},
        )
        if session.customer:
            self.db.set_billing_customer(user["id"], str(session.customer))
        return BillingSession(url=str(session.url), mode="stripe")

    def create_portal(self, user: dict[str, str]) -> BillingSession:
        subscription = self.db.get_subscription(user["id"])
        if settings.billing_mode == "mock" or not settings.stripe_secret_key:
            return BillingSession(
                url=f"{settings.public_base_url}/billing/mock-portal?email={user['email']}",
                mode="mock",
            )

        customer_id = subscription.get("billing_customer_id")
        if not customer_id:
            raise ValueError("No billing customer is attached to this account yet")
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.billing_portal_return_url,
        )
        return BillingSession(url=str(session.url), mode="stripe")

    def handle_webhook(self, payload: bytes, signature: str | None = None) -> dict[str, str]:
        if settings.billing_mode == "mock" or not settings.stripe_secret_key:
            # Mock mode: parse the raw JSON body directly.
            # Validate that the payload is well-formed JSON and that required
            # fields are present and sane before touching the database.
            try:
                data = json.loads(payload.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError("Mock webhook payload is not valid JSON") from exc

            email = data.get("email", "")
            if not isinstance(email, str) or not email.strip():
                raise ValueError("Mock webhook payload must include a non-empty 'email' field")

            # Import here to avoid a circular import at module load time.
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

        if not settings.stripe_webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")

        event = stripe.Webhook.construct_event(payload=payload, sig_header=signature or "", secret=settings.stripe_webhook_secret)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("metadata", {}).get("user_id")
            if user_id:
                self.db.update_subscription_state(
                    user_id=user_id,
                    status_value="active",
                    customer_id=session.get("customer"),
                    subscription_id=session.get("subscription"),
                )
        elif event["type"] in {"customer.subscription.updated", "customer.subscription.deleted"}:
            subscription = event["data"]["object"]
            user_id = subscription.get("metadata", {}).get("user_id")
            status_value = _map_stripe_status(subscription.get("status"))
            if user_id:
                self.db.update_subscription_state(
                    user_id=user_id,
                    status_value=status_value,
                    customer_id=subscription.get("customer"),
                    subscription_id=subscription.get("id"),
                )

        return {"status": "active"}


def _map_stripe_status(value: str | None) -> str:
    if value in {"active", "trialing", "past_due", "canceled"}:
        return value
    if value in {"unpaid", "incomplete", "incomplete_expired"}:
        return "past_due"
    return "canceled"
