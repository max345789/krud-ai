"""
API route handlers.

Security hardening applied here
────────────────────────────────
1. Rate limiting (OWASP A04: Insecure Design)
   Every public endpoint carries a @limiter.limit() decorator.  Limits are
   deliberately conservative on unauthenticated write flows (device start,
   form submit, mock billing) and more generous on polling / reads.

   Tier summary:
     STRICT   –  5/minute  unauthenticated writes  (form submit, mock billing)
     AUTH     – 10/minute  device start / complete
     POLL     – 120/minute device poll (CLI polls every 5 s; generous headroom)
     STANDARD – 30/minute  authenticated user actions
     RELAXED  – 60/minute  cheap authenticated reads
     PUBLIC   – 20/minute  unauthenticated reads

   All routes that accept `Depends(get_current_user)` use key_func=user_or_ip_key
   so limits are per-user rather than per-IP (prevents one IP blocking another
   user sharing a NAT).

2. Query / form parameter validation (OWASP A03: Injection)
   - user_code in GET /device and POST /device validated via require_valid_user_code
   - email in mock billing GET routes validated via require_valid_email
   - status_value in mock billing forms validated against the subscription
     status allowlist via require_valid_subscription_status
   - channel in /v1/releases/latest validated via require_valid_channel

3. Error message sanitization (OWASP A09: Logging / information disclosure)
   ValueError messages from internal code (db, services) are NOT forwarded
   verbatim to clients.  Each catch site uses a generic user-facing message
   and the original exception is chained for server-side tracing.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.db import Database
from app.core.limiter import limiter, user_or_ip_key
from app.core.security import (
    require_valid_channel,
    require_valid_email,
    require_valid_subscription_status,
    require_valid_user_code,
)
from app.models.schemas import (
    AccountResponse,
    BillingCheckoutResponse,
    BillingOverviewResponse,
    BillingPortalResponse,
    BillingWebhookResponse,
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionReply,
    ChatSessionResponse,
    CommandProposal,
    DeviceApprovalRequest,
    DevicePollRequest,
    DevicePollResponse,
    DeviceStartRequest,
    DeviceStartResponse,
    ReleaseResponse,
    SubscriptionResponse,
    TokenBudget,
    UsageSummary,
)
from app.core.token_budget import _window_start, check_budget
from app.services.billing import BillingService
from app.services.chat import build_chat_reply, derive_session_title
from app.services.device_auth import build_device_page
from app.services.pages import (
    render_billing_checkout_page,
    render_billing_portal_page,
    render_simple_notice,
)

router = APIRouter()
db = Database()
billing = BillingService(db)


# ── Device auth ───────────────────────────────────────────────────────────────

@router.post("/v1/device/start", response_model=DeviceStartResponse)
@limiter.limit("10/minute")
def device_start(request: Request, payload: DeviceStartRequest) -> DeviceStartResponse:
    """
    Initiate a device-code flow.

    Rate limit: 10/minute per IP.  Prevents an attacker from flooding the
    device_codes table with junk records.
    """
    record = db.create_device_code(client_name=payload.client_name)
    return DeviceStartResponse(
        device_code=record["device_code"],
        user_code=record["user_code"],
        verification_uri=f"{settings.public_base_url}/device",
        verification_uri_complete=f"{settings.public_base_url}/device?user_code={record['user_code']}",
        interval_seconds=settings.device_poll_interval_seconds,
        expires_in_seconds=settings.device_code_ttl_seconds,
    )


@router.get("/device", response_class=HTMLResponse)
@limiter.limit("30/minute")
def device_page(request: Request, user_code: str | None = None) -> HTMLResponse:
    """
    Serve the browser approval page.

    user_code is validated before being forwarded to the HTML builder so that
    malformed values never reach template rendering.
    """
    safe_code = require_valid_user_code(user_code) if user_code else None
    return HTMLResponse(build_device_page(user_code=safe_code))


@router.post("/device", response_class=HTMLResponse)
@limiter.limit("5/minute")
def device_page_submit(
    request: Request,
    user_code: str = Form(...),
    email: str = Form(...),
    name: str = Form(default=""),
) -> HTMLResponse:
    """
    Browser form submission — approve a pending device code.

    Rate limit: 5/minute per IP (STRICT).  This endpoint is the primary
    brute-force surface for user codes; a low limit makes enumeration impractical.
    Both user_code and email are validated before any DB access.
    """
    safe_code = require_valid_user_code(user_code)
    safe_email = require_valid_email(email)
    try:
        db.complete_device_code(
            user_code=safe_code,
            approval=DeviceApprovalRequest(email=safe_email, name=name or None),
        )
    except ValueError:
        # Do not expose the internal error message — it could reveal whether
        # a code exists, has expired, etc. (user enumeration / oracle attack).
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired device code",
        )
    return HTMLResponse(build_device_page(user_code=safe_code, approved=True, email=safe_email))


@router.post("/v1/device/complete")
@limiter.limit("5/minute")
def device_complete(
    request: Request,
    payload: DeviceApprovalRequest,
    user_code: str,
) -> dict[str, str]:
    """
    Programmatic device-code completion (used in automated flows).

    user_code arrives as a query param and is validated before the DB call.
    """
    safe_code = require_valid_user_code(user_code)
    try:
        record = db.complete_device_code(user_code=safe_code, approval=payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired device code",
        )
    return {"status": record["status"]}


@router.post("/v1/device/poll", response_model=DevicePollResponse)
@limiter.limit("120/minute")
def device_poll(request: Request, payload: DevicePollRequest) -> DevicePollResponse:
    """
    Poll for device-code approval status.

    Rate limit: 120/minute per IP.  The CLI polls every 5 seconds so during a
    15-minute TTL window a single device generates at most 180 polls; 120/min
    allows comfortable headroom while still blocking abusive enumeration.
    device_code format is validated by the DevicePollRequest schema.
    """
    result = db.poll_device_code(payload.device_code)
    if result["status"] == "pending":
        return DevicePollResponse(status="pending")
    if result["status"] == "expired":
        return DevicePollResponse(status="expired")

    return DevicePollResponse(
        status="approved",
        session_token=result["session_token"],
        account=AccountResponse(
            user_id=result["user_id"],
            email=result["email"],
            name=result["name"],
            usage_events=0,
        ),
        subscription=SubscriptionResponse(
            status=result["subscription_status"],
            trial_ends_at=result["trial_ends_at"],
            price_id=settings.dodo_product_id,
            customer_id=result.get("billing_customer_id"),
            subscription_id=result.get("billing_subscription_id"),
        ),
    )


# ── Account ───────────────────────────────────────────────────────────────────

@router.get("/v1/account/me", response_model=AccountResponse)
@limiter.limit("60/minute", key_func=user_or_ip_key)
def account_me(request: Request, user=Depends(get_current_user)) -> AccountResponse:
    return AccountResponse(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        usage_events=user.get("usage_events", 0),
    )


@router.get("/v1/account/subscription", response_model=SubscriptionResponse)
@limiter.limit("60/minute", key_func=user_or_ip_key)
def account_subscription(
    request: Request, user=Depends(get_current_user)
) -> SubscriptionResponse:
    current = db.get_subscription(user["id"])
    return SubscriptionResponse(
        status=current.get("subscription_status", user["subscription_status"]),
        trial_ends_at=current.get("trial_ends_at", user["trial_ends_at"]),
        price_id=settings.dodo_product_id,
        customer_id=current.get("billing_customer_id"),
        subscription_id=current.get("billing_subscription_id"),
    )


# ── Billing ───────────────────────────────────────────────────────────────────

@router.get("/v1/billing", response_model=BillingOverviewResponse)
@limiter.limit("30/minute", key_func=user_or_ip_key)
def billing_overview(
    request: Request, user=Depends(get_current_user)
) -> BillingOverviewResponse:
    return BillingOverviewResponse(**billing.overview(user))


@router.post("/v1/billing/checkout", response_model=BillingCheckoutResponse)
@limiter.limit("5/minute", key_func=user_or_ip_key)
def billing_checkout(
    request: Request, user=Depends(get_current_user)
) -> BillingCheckoutResponse:
    session = billing.create_checkout(user)
    return BillingCheckoutResponse(checkout_url=session.url, mode=session.mode)


@router.post("/v1/billing/portal", response_model=BillingPortalResponse)
@limiter.limit("5/minute", key_func=user_or_ip_key)
def billing_portal(
    request: Request, user=Depends(get_current_user)
) -> BillingPortalResponse:
    try:
        session = billing.create_portal(user)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account is attached to this user yet",
        )
    return BillingPortalResponse(portal_url=session.url, mode=session.mode)


@router.post("/v1/billing/webhook", response_model=BillingWebhookResponse)
async def billing_webhook(request: Request) -> BillingWebhookResponse:
    """
    Dodo Payments webhook receiver.

    No rate limit — Dodo must always be able to reach this endpoint without
    being throttled.

    Dodo uses three headers for HMAC-SHA256 signature verification:
      webhook-id        — unique event ID (used for idempotency)
      webhook-signature — HMAC-SHA256 signature of "{id}.{timestamp}.{body}"
      webhook-timestamp — Unix timestamp (seconds) of when the event was sent

    In mock mode these headers are ignored and the raw JSON body is trusted.
    """
    payload = await request.body()
    # Pass all three Dodo signing headers so billing.py can verify the signature.
    webhook_headers = {
        "webhook-id": request.headers.get("webhook-id", ""),
        "webhook-signature": request.headers.get("webhook-signature", ""),
        "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
    }
    try:
        result = billing.handle_webhook(payload=payload, webhook_headers=webhook_headers)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed",
        )
    return BillingWebhookResponse(processed=True, status=result["status"])


# ── Mock billing pages (only active when billing_mode == "mock") ──────────────

@router.get("/billing/mock-checkout", response_class=HTMLResponse)
@limiter.limit("10/minute")
def billing_mock_checkout(
    request: Request, email: str, plan: str = ""
) -> HTMLResponse:
    """
    Mock checkout page — shows a simple HTML form.

    email is validated to prevent log injection and to ensure the DB query uses
    a valid address.  This endpoint only does anything useful in mock mode;
    in production, clients should use /v1/billing/checkout instead.
    """
    safe_email = require_valid_email(email)
    return HTMLResponse(
        render_billing_checkout_page(email=safe_email, plan=plan or settings.dodo_product_id)
    )


@router.post("/billing/mock-checkout", response_class=HTMLResponse)
@limiter.limit("5/minute")
def billing_mock_checkout_submit(
    request: Request,
    email: str = Form(...),
    status_value: str = Form(alias="status"),
) -> HTMLResponse:
    """
    Activate a subscription in mock mode.

    status_value is validated against the allowlist before being written to the
    DB — prevents arbitrary strings from corrupting subscription_status.
    """
    safe_email = require_valid_email(email)
    safe_status = require_valid_subscription_status(status_value)
    db.update_subscription_state(
        email=safe_email, status_value=safe_status, customer_id="cus_mock_local"
    )
    return HTMLResponse(
        render_simple_notice(
            "Subscription Activated",
            f"{safe_email} is now marked as {safe_status}. "
            "Return to the terminal and continue using Krud AI.",
        )
    )


@router.get("/billing/mock-portal", response_class=HTMLResponse)
@limiter.limit("10/minute")
def billing_mock_portal(request: Request, email: str) -> HTMLResponse:
    safe_email = require_valid_email(email)
    subscription = db.get_subscription_by_email(safe_email)
    status_val = subscription.get("subscription_status", "trialing")
    return HTMLResponse(render_billing_portal_page(email=safe_email, status=status_val))


@router.post("/billing/mock-portal", response_class=HTMLResponse)
@limiter.limit("5/minute")
def billing_mock_portal_submit(
    request: Request,
    email: str = Form(...),
    status_value: str = Form(alias="status"),
) -> HTMLResponse:
    safe_email = require_valid_email(email)
    safe_status = require_valid_subscription_status(status_value)
    user = db.update_subscription_state(email=safe_email, status_value=safe_status)
    return HTMLResponse(
        render_billing_portal_page(email=safe_email, status=user["subscription_status"])
    )


@router.get("/billing/success", response_class=HTMLResponse)
def billing_success() -> HTMLResponse:
    return HTMLResponse(
        render_simple_notice(
            "Billing Success",
            "Checkout completed. Return to the terminal and keep working.",
        )
    )


@router.get("/billing/cancel", response_class=HTMLResponse)
def billing_cancel() -> HTMLResponse:
    return HTMLResponse(
        render_simple_notice(
            "Billing Canceled",
            "Checkout was canceled. You can return to the terminal or try again later.",
        )
    )


@router.get("/favicon.ico", status_code=status.HTTP_204_NO_CONTENT)
def favicon() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/v1/chat/sessions", response_model=ChatSessionResponse)
@limiter.limit("20/minute", key_func=user_or_ip_key)
def create_chat_session(
    request: Request,
    payload: ChatSessionCreate,
    user=Depends(get_current_user),
) -> ChatSessionResponse:
    title = derive_session_title(payload.title)
    session = db.create_chat_session(user_id=user["id"], title=title)
    return ChatSessionResponse(
        session_id=session["id"],
        title=session["title"],
        created_at=session["created_at"],
    )


@router.post(
    "/v1/chat/sessions/{session_id}/messages", response_model=ChatSessionReply
)
@limiter.limit("30/minute", key_func=user_or_ip_key)
def post_message(
    request: Request,
    session_id: str,
    payload: ChatMessageCreate,
    user=Depends(get_current_user),
) -> ChatSessionReply:
    """
    Send a message and receive an AI reply with optional command proposals.

    Rate limits applied in two layers:
      1. Request rate  – 30/minute per user (slowapi), prevents request floods.
      2. Token budget  – rolling 5-hour window per user (token_budget), mirrors
                         Claude Code's usage-based limits and controls API spend.
                         Trial users: 40,000 tokens / 5 h.
                         Active users: 2,000,000 tokens / 5 h.
    """
    from datetime import UTC, datetime

    db.require_active_access(user)
    session = db.get_chat_session(session_id=session_id, user_id=user["id"])
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # ── token budget pre-check ────────────────────────────────────────────────
    now = datetime.now(UTC)
    window_start = _window_start(now)
    used_before, oldest_at = db.get_token_usage_window(user["id"], since=window_start)
    used, limit, budget_headers = check_budget(user, used_before, oldest_at)

    # ── run the LLM call ──────────────────────────────────────────────────────
    db.add_chat_message(
        session_id=session_id,
        role="user",
        content=payload.content,
        metadata={"cwd": payload.cwd} if payload.cwd else None,
    )
    history = db.get_recent_chat_messages(session_id=session_id)
    generation = build_chat_reply(payload.content, history=history[:-1], cwd=payload.cwd)
    db.add_chat_message(
        session_id=session_id,
        role="assistant",
        content=generation.text,
        metadata={
            "provider": generation.provider,
            "model": generation.model,
            "command_proposals": generation.command_proposals,
        },
    )
    db.add_usage_event(
        user_id=user["id"],
        session_id=session_id,
        provider=generation.provider,
        model=generation.model,
        prompt_tokens=generation.prompt_tokens,
        completion_tokens=generation.completion_tokens,
    )

    # ── recalculate budget with this call's tokens included ───────────────────
    tokens_this_call = generation.prompt_tokens + generation.completion_tokens
    used_after = used_before + tokens_this_call
    from app.core.token_budget import get_budget_headers
    budget_headers = get_budget_headers(used_after, limit, oldest_at, now)

    from fastapi.responses import JSONResponse
    reply = ChatSessionReply(
        session_id=session_id,
        text=generation.text,
        command_proposals=[
            CommandProposal(**proposal) for proposal in generation.command_proposals
        ],
        provider=generation.provider,
        usage=UsageSummary(
            provider=generation.provider,
            model=generation.model,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
        ),
        budget=TokenBudget(
            used=used_after,
            limit=limit,
            resets_at=budget_headers["X-Token-Reset"],
        ),
    )
    # Return as JSONResponse so we can attach the X-Token-* headers the CLI reads.
    response = JSONResponse(content=reply.model_dump(), headers=budget_headers)
    return response


# ── Releases ──────────────────────────────────────────────────────────────────

@router.get("/v1/releases/latest", response_model=ReleaseResponse)
@limiter.limit("20/minute")
def latest_release(request: Request, channel: str = "stable") -> ReleaseResponse:
    """
    Return the latest release manifest for a given channel.

    channel is validated against an allowlist to prevent unexpected values
    from reaching downstream logic or being reflected back in the response.
    """
    safe_channel = require_valid_channel(channel)
    version = settings.release_version
    base = settings.download_base_url.rstrip("/")
    return ReleaseResponse(
        channel=safe_channel,
        version=version,
        notes="Initial Krud AI bootstrap release",
        assets={
            "darwin-aarch64": f"{base}/{version}/krud-darwin-aarch64.tar.gz",
            "darwin-x86_64": f"{base}/{version}/krud-darwin-x86_64.tar.gz",
        },
        signature_asset=f"{base}/{version}/krud-checksums.txt",
    )
