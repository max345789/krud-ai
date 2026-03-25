from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.db import Database
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
    UsageSummary,
)
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


@router.post("/v1/device/start", response_model=DeviceStartResponse)
def device_start(payload: DeviceStartRequest) -> DeviceStartResponse:
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
def device_page(user_code: str | None = None) -> HTMLResponse:
    return HTMLResponse(build_device_page(user_code=user_code))


@router.post("/device", response_class=HTMLResponse)
def device_page_submit(
    user_code: str = Form(...),
    email: str = Form(...),
    name: str = Form(default=""),
) -> HTMLResponse:
    try:
        db.complete_device_code(
            user_code=user_code,
            approval=DeviceApprovalRequest(email=email, name=name or None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return HTMLResponse(build_device_page(user_code=user_code, approved=True, email=email))


@router.get("/billing/mock-checkout", response_class=HTMLResponse)
def billing_mock_checkout(email: str, plan: str = "") -> HTMLResponse:
    return HTMLResponse(render_billing_checkout_page(email=email, plan=plan or settings.stripe_price_id))


@router.post("/billing/mock-checkout", response_class=HTMLResponse)
def billing_mock_checkout_submit(email: str = Form(...), status_value: str = Form(alias="status")) -> HTMLResponse:
    db.update_subscription_state(email=email.lower(), status_value=status_value, customer_id="cus_mock_local")
    return HTMLResponse(
        render_simple_notice(
            "Subscription Activated",
            f"{email} is now marked as {status_value}. Return to the terminal and continue using Krud AI.",
        )
    )


@router.get("/billing/mock-portal", response_class=HTMLResponse)
def billing_mock_portal(email: str) -> HTMLResponse:
    subscription = db.get_subscription_by_email(email.lower())
    status_value = subscription.get("subscription_status", "trialing")
    return HTMLResponse(render_billing_portal_page(email=email, status=status_value))


@router.post("/billing/mock-portal", response_class=HTMLResponse)
def billing_mock_portal_submit(email: str = Form(...), status_value: str = Form(alias="status")) -> HTMLResponse:
    user = db.update_subscription_state(email=email.lower(), status_value=status_value)
    return HTMLResponse(render_billing_portal_page(email=email, status=user["subscription_status"]))


@router.get("/billing/success", response_class=HTMLResponse)
def billing_success() -> HTMLResponse:
    return HTMLResponse(render_simple_notice("Billing Success", "Checkout completed. Return to the terminal and keep working."))


@router.get("/billing/cancel", response_class=HTMLResponse)
def billing_cancel() -> HTMLResponse:
    return HTMLResponse(render_simple_notice("Billing Canceled", "Checkout was canceled. You can return to the terminal or try again later."))


@router.get("/favicon.ico", status_code=status.HTTP_204_NO_CONTENT)
def favicon() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/v1/device/complete")
def device_complete(payload: DeviceApprovalRequest, user_code: str) -> dict[str, str]:
    try:
        record = db.complete_device_code(user_code=user_code, approval=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": record["status"]}


@router.post("/v1/device/poll", response_model=DevicePollResponse)
def device_poll(payload: DevicePollRequest) -> DevicePollResponse:
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
            price_id=settings.stripe_price_id,
            customer_id=result.get("billing_customer_id"),
            subscription_id=result.get("billing_subscription_id"),
        ),
    )


@router.get("/v1/account/me", response_model=AccountResponse)
def account_me(user=Depends(get_current_user)) -> AccountResponse:
    return AccountResponse(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        usage_events=user.get("usage_events", 0),
    )


@router.get("/v1/account/subscription", response_model=SubscriptionResponse)
def account_subscription(user=Depends(get_current_user)) -> SubscriptionResponse:
    current = db.get_subscription(user["id"])
    return SubscriptionResponse(
        status=current.get("subscription_status", user["subscription_status"]),
        trial_ends_at=current.get("trial_ends_at", user["trial_ends_at"]),
        price_id=settings.stripe_price_id,
        customer_id=current.get("billing_customer_id"),
        subscription_id=current.get("billing_subscription_id"),
    )


@router.get("/v1/billing", response_model=BillingOverviewResponse)
def billing_overview(user=Depends(get_current_user)) -> BillingOverviewResponse:
    return BillingOverviewResponse(**billing.overview(user))


@router.post("/v1/billing/checkout", response_model=BillingCheckoutResponse)
def billing_checkout(user=Depends(get_current_user)) -> BillingCheckoutResponse:
    session = billing.create_checkout(user)
    return BillingCheckoutResponse(checkout_url=session.url, mode=session.mode)


@router.post("/v1/billing/portal", response_model=BillingPortalResponse)
def billing_portal(user=Depends(get_current_user)) -> BillingPortalResponse:
    try:
        session = billing.create_portal(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BillingPortalResponse(portal_url=session.url, mode=session.mode)


@router.post("/v1/billing/webhook", response_model=BillingWebhookResponse)
async def billing_webhook(request: Request) -> BillingWebhookResponse:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        result = billing.handle_webhook(payload=payload, signature=signature)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BillingWebhookResponse(processed=True, status=result["status"])


@router.post("/v1/chat/sessions", response_model=ChatSessionResponse)
def create_chat_session(payload: ChatSessionCreate, user=Depends(get_current_user)) -> ChatSessionResponse:
    title = derive_session_title(payload.title)
    session = db.create_chat_session(user_id=user["id"], title=title)
    return ChatSessionResponse(session_id=session["id"], title=session["title"], created_at=session["created_at"])


@router.post("/v1/chat/sessions/{session_id}/messages", response_model=ChatSessionReply)
def post_message(
    session_id: str,
    payload: ChatMessageCreate,
    user=Depends(get_current_user),
) -> ChatSessionReply:
    db.require_active_access(user)
    session = db.get_chat_session(session_id=session_id, user_id=user["id"])
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

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

    return ChatSessionReply(
        session_id=session_id,
        text=generation.text,
        command_proposals=[CommandProposal(**proposal) for proposal in generation.command_proposals],
        provider=generation.provider,
        usage=UsageSummary(
            provider=generation.provider,
            model=generation.model,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
        ),
    )


@router.get("/v1/releases/latest", response_model=ReleaseResponse)
def latest_release(channel: str = "stable") -> ReleaseResponse:
    version = settings.release_version
    base = settings.download_base_url.rstrip("/")
    return ReleaseResponse(
        channel=channel,
        version=version,
        notes="Initial Krud AI bootstrap release",
        assets={
            "darwin-aarch64": f"{base}/{version}/krud-darwin-aarch64.tar.gz",
            "darwin-x86_64": f"{base}/{version}/krud-darwin-x86_64.tar.gz",
        },
        signature_asset=f"{base}/{version}/krud-checksums.txt",
    )
