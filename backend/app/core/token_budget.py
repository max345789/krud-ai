"""
Claude Code-style rolling token budget.

How it works
────────────
Every LLM response records prompt_tokens + completion_tokens in usage_events.
Before each chat request we sum all tokens used in the last N hours (rolling
window, same as Claude Code's 5-hour window) and compare to the tier limit.

Tiers
─────
  trialing  → KRUD_TOKEN_BUDGET_TRIAL  (default 40,000 / 5 h)
  active    → KRUD_TOKEN_BUDGET_ACTIVE (default 2,000,000 / 5 h)
  past_due  → treated as trial (reduced access)
  canceled  → 0 (blocked at subscription check before we get here)

Response headers (added by the chat route so the CLI can render a progress bar)
───────────────────────────────────────────────────────────────────────────────
  X-Token-Used      – tokens consumed in the current window
  X-Token-Limit     – tier limit for this window
  X-Token-Reset     – ISO-8601 UTC timestamp when the oldest event ages out
                      (i.e. the window will shrink and free up budget)
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import settings


def _limit_for(subscription_status: str, plan: str = "free") -> int:
    if subscription_status == "active":
        if plan == "pilot":
            return settings.token_budget_pilot
        if plan == "builder":
            return settings.token_budget_builder
        # free plan active users get the free budget
        return settings.token_budget_free
    # trialing, past_due, or anything unexpected → restricted (free) budget
    return settings.token_budget_free


def _window_start(now: datetime) -> datetime:
    return now - timedelta(hours=settings.token_budget_window_hours)


def get_budget_headers(
    used: int,
    limit: int,
    oldest_event_at: str | None,
    now: datetime,
) -> dict[str, str]:
    """
    Build the three X-Token-* headers to attach to a chat response.

    oldest_event_at is the ISO timestamp of the earliest usage event inside
    the current window.  When it ages out the budget rolls back by that
    event's token count — so it's a useful "resets at" hint for the CLI.
    """
    if oldest_event_at:
        # The window advances as the oldest event falls out of the 5-hour range.
        if isinstance(oldest_event_at, datetime):
            reset_dt = oldest_event_at + timedelta(hours=settings.token_budget_window_hours)
        else:
            reset_dt = datetime.fromisoformat(oldest_event_at) + timedelta(
                hours=settings.token_budget_window_hours
            )
    else:
        # No events yet — window resets from now (effectively immediate).
        reset_dt = now + timedelta(hours=settings.token_budget_window_hours)

    return {
        "X-Token-Used": str(used),
        "X-Token-Limit": str(limit),
        "X-Token-Reset": reset_dt.astimezone(UTC).isoformat(),
    }


def check_budget(
    user: dict,
    used: int,
    oldest_event_at: str | None,
) -> tuple[int, int, dict[str, str]]:
    """
    Raise HTTP 429 if the user has exhausted their rolling token budget.

    Returns (used, limit, headers) on success so the caller can attach
    the headers to the response without a second DB call.

    The 429 body mirrors Claude Code's format:
      {
        "detail": "Token limit reached",
        "used": 41200,
        "limit": 40000,
        "resets_at": "2026-03-25T11:45:00+00:00"
      }
    """
    now = datetime.now(UTC)
    limit = _limit_for(user["subscription_status"], user.get("plan", "free"))
    headers = get_budget_headers(used, limit, oldest_event_at, now)

    if used >= limit:
        reset_iso = headers["X-Token-Reset"]
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Token limit reached. Your budget resets on a rolling 5-hour window.",
                "used": used,
                "limit": limit,
                "resets_at": reset_iso,
            },
            headers={"Retry-After": "300", **headers},
        )

    return used, limit, headers
