from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


SubscriptionStatus = Literal["trialing", "active", "past_due", "canceled"]


class DeviceStartRequest(BaseModel):
    client_name: str = Field(default="krud-cli", min_length=2, max_length=120)


class DeviceStartResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    interval_seconds: int
    expires_in_seconds: int


class DeviceApprovalRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)


class DevicePollRequest(BaseModel):
    device_code: str


class AccountResponse(BaseModel):
    user_id: str
    email: EmailStr
    name: str | None = None
    usage_events: int = 0


class SubscriptionResponse(BaseModel):
    status: SubscriptionStatus
    trial_ends_at: datetime
    price_id: str
    customer_id: str | None = None
    subscription_id: str | None = None


class DevicePollResponse(BaseModel):
    status: Literal["pending", "expired", "approved"]
    session_token: str | None = None
    account: AccountResponse | None = None
    subscription: SubscriptionResponse | None = None


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    cwd: str | None = Field(default=None, max_length=1000)


class CommandProposal(BaseModel):
    command: str
    rationale: str
    risk: Literal["low", "medium", "high"]


class UsageSummary(BaseModel):
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ChatSessionReply(BaseModel):
    session_id: str
    text: str
    command_proposals: list[CommandProposal]
    provider: str
    usage: UsageSummary


class BillingOverviewResponse(BaseModel):
    checkout_enabled: bool
    portal_enabled: bool
    subscription: SubscriptionResponse
    usage_events: int


class BillingCheckoutResponse(BaseModel):
    checkout_url: str
    mode: Literal["mock", "stripe"]


class BillingPortalResponse(BaseModel):
    portal_url: str
    mode: Literal["mock", "stripe"]


class BillingWebhookResponse(BaseModel):
    processed: bool
    status: SubscriptionStatus


class ReleaseResponse(BaseModel):
    channel: str
    version: str
    notes: str
    assets: dict[str, str]
    signature_asset: str
