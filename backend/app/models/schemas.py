"""
Pydantic request/response schemas.

Security notes (OWASP A03: Injection / A08: Data Integrity)
────────────────────────────────────────────────────────────
- Every user-supplied string field has an explicit length upper bound to prevent
  oversized payloads from reaching business logic or the database.
- @field_validator methods call the shared validators in core/security.py so
  that constraint logic lives in one place only.
- Extra fields are forbidden on all request models (model_config) so that
  unexpected keys are rejected rather than silently ignored — this prevents
  parameter pollution attacks.
- Response models do NOT forbid extra fields (they only serialize known fields,
  so extra DB columns are harmless).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import (
    validate_client_name,
    validate_cwd,
    validate_device_code,
    validate_no_null_bytes,
    validate_user_code,
)

SubscriptionStatus = Literal["trialing", "active", "past_due", "canceled"]

# Shared config that forbids extra fields on inbound request bodies.
_STRICT = ConfigDict(extra="forbid")


# ── Device auth ───────────────────────────────────────────────────────────────

class DeviceStartRequest(BaseModel):
    """
    Initiates a device-code flow.

    client_name is included in logs and the device_codes table; restrict it to
    safe printable characters to prevent log injection.
    """
    model_config = _STRICT

    client_name: str = Field(default="krud-cli", min_length=2, max_length=64)

    @field_validator("client_name")
    @classmethod
    def _validate_client_name(cls, v: str) -> str:
        return validate_client_name(v)


class DeviceStartResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    interval_seconds: int
    expires_in_seconds: int


class DeviceApprovalRequest(BaseModel):
    """
    Submitted by the browser when the user approves a device login.

    EmailStr validates the full RFC-5322 format.  name is optional display
    text; max_length prevents oversized values reaching the DB.
    """
    model_config = _STRICT

    email: EmailStr
    name: str | None = Field(default=None, max_length=120)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        # Strip whitespace; reject null bytes (control character injection).
        if v is None:
            return None
        if "\x00" in v:
            raise ValueError("Null bytes are not permitted")
        return v.strip() or None


class DevicePollRequest(BaseModel):
    """
    CLI polls this repeatedly until the device is approved or expires.

    device_code is validated against the format produced by
    secrets.token_urlsafe(24) so random garbage is rejected before
    hitting the database.
    """
    model_config = _STRICT

    # min/max enforce reasonable bounds before the regex runs.
    device_code: str = Field(min_length=20, max_length=64)

    @field_validator("device_code")
    @classmethod
    def _validate_device_code(cls, v: str) -> str:
        return validate_device_code(v)


# ── Account ───────────────────────────────────────────────────────────────────

class AccountUpdateRequest(BaseModel):
    model_config = _STRICT
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("Null bytes are not permitted")
        return v.strip()


class AccountResponse(BaseModel):
    user_id: str
    email: EmailStr
    name: str | None = None
    usage_events: int = 0


class SubscriptionResponse(BaseModel):
    status: SubscriptionStatus
    trial_ends_at: datetime
    price_id: str  # Dodo Payments product ID (formerly Stripe price ID)
    customer_id: str | None = None
    subscription_id: str | None = None


class DevicePollResponse(BaseModel):
    status: Literal["pending", "expired", "approved"]
    session_token: str | None = None
    account: AccountResponse | None = None
    subscription: SubscriptionResponse | None = None


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    """
    title is optional display text; strip and cap to prevent oversized values.
    Extra fields forbidden so clients cannot smuggle in unexpected keys.
    """
    model_config = _STRICT

    title: str | None = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime


class ChatSessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    message_count: int = 0
    tokens_used: int = 0


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionSummary]


class ChatMessageCreate(BaseModel):
    """
    content is the user's message to the LLM.
    cwd is forwarded as LLM system context — reject control characters that
    could be used for prompt injection via newline/escape sequences (OWASP A03).
    """
    model_config = _STRICT

    content: str = Field(min_length=1, max_length=4000)
    # cwd length capped at 512 — absolute paths on any real OS fit comfortably.
    cwd: str | None = Field(default=None, max_length=512)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, v: str) -> str:
        return validate_no_null_bytes(v)

    @field_validator("cwd")
    @classmethod
    def _validate_cwd(cls, v: str | None) -> str | None:
        return validate_cwd(v)


class CommandProposal(BaseModel):
    command: str
    rationale: str
    risk: Literal["low", "medium", "high"]


class UsageSummary(BaseModel):
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class TokenBudget(BaseModel):
    used: int
    limit: int
    resets_at: str  # ISO-8601 UTC — when the oldest event in the window ages out


class ChatSessionReply(BaseModel):
    session_id: str
    text: str
    command_proposals: list[CommandProposal]
    provider: str
    usage: UsageSummary
    budget: TokenBudget


# ── Billing ───────────────────────────────────────────────────────────────────

class BillingOverviewResponse(BaseModel):
    checkout_enabled: bool
    portal_enabled: bool
    subscription: SubscriptionResponse
    usage_events: int


class BillingCheckoutResponse(BaseModel):
    checkout_url: str
    mode: Literal["mock", "dodo"]


class BillingPortalResponse(BaseModel):
    portal_url: str
    mode: Literal["mock", "dodo"]


class BillingWebhookResponse(BaseModel):
    processed: bool
    # "skipped" means the event was acknowledged but required no DB change
    # (unknown event type or unresolvable user).  All others are subscription states.
    status: SubscriptionStatus | Literal["skipped"]


# ── Release ───────────────────────────────────────────────────────────────────

class ReleaseResponse(BaseModel):
    channel: str
    version: str
    notes: str
    assets: dict[str, str]
    signature_asset: str
