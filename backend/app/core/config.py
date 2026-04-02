"""
Application settings loaded from environment variables.

Security notes
──────────────
- All sensitive fields (API keys, webhook secrets) are sourced exclusively from
  environment variables.  No secrets are hard-coded here.
- __repr__ and __str__ are overridden to mask secrets so they cannot leak into
  logs, error reports, or stack traces (OWASP A02: Cryptographic Failures /
  A09: Security Logging and Monitoring Failures).
- The settings object is frozen; values cannot be mutated at runtime.

Environment variables
─────────────────────
  OPENAI_API_KEY           – required for LLM calls; if absent, heuristic fallback runs
  RAZORPAY_KEY_ID          – required for real billing; if absent, mock billing is used
  RAZORPAY_KEY_SECRET      – Razorpay key secret (keep in Render secret env vars)
  RAZORPAY_WEBHOOK_SECRET  – required to verify Razorpay webhook signatures
  RAZORPAY_PLAN_ID         – subscription plan ID from Razorpay dashboard
  DATABASE_URL             – PostgreSQL connection string for production
  KRUD_DATABASE_PATH       – local sqlite path for development and tests
  KRUD_ALLOWED_ORIGINS     – comma-separated extra CORS origins (default: public_base_url)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _mask(value: str | None, visible: int = 4) -> str:
    """
    Return a masked representation of a secret string for safe logging.

    Shows the first `visible` characters followed by '***'.  If the secret is
    shorter than `visible` characters, returns '***' entirely so that short
    secrets are not revealed.
    """
    if not value:
        return "None"
    if len(value) <= visible:
        return "***"
    return value[:visible] + "***"


@dataclass(frozen=True)
class Settings:
    # ── server ───────────────────────────────────────────────────────────────
    api_host: str = os.getenv("KRUD_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("KRUD_API_PORT", "8000"))
    public_base_url: str = os.getenv("KRUD_PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    # ── browser-facing hosts ────────────────────────────────────────────────
    # device_base_url is the explicit host used in the CLI login link. It can
    # be a dedicated auth subdomain or a frontend domain, as long as /cli-auth
    # and /device resolve to this backend.
    device_base_url_override: str = os.getenv("KRUD_DEVICE_BASE_URL", "")
    # Backward-compatible fallback for older deployments that used the more
    # generic frontend URL name for the device approval page.
    frontend_url: str = os.getenv("KRUD_FRONTEND_URL", "")

    # ── release distribution ─────────────────────────────────────────────────
    download_base_url: str = os.getenv(
        "KRUD_DOWNLOAD_BASE_URL",
        "https://github.com/max345789/krud-ai/releases/download",
    )
    release_version: str = os.getenv("KRUD_RELEASE_VERSION", "0.1.0")

    # ── database ─────────────────────────────────────────────────────────────
    # PostgreSQL connection string (Supabase). Preferred in production.
    # Example: postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    database_url: str = os.getenv("DATABASE_URL", "")
    # Local sqlite path used by tests and local development when DATABASE_URL is
    # not configured.
    database_path: str = os.getenv("KRUD_DATABASE_PATH", "")

    # ── LLM — key is read from env only, never hard-coded ────────────────────
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))

    # ── billing — keys are read from env only, never hard-coded ─────────────
    # billing_mode: "mock" (local dev, no real payments) or "razorpay" (production)
    billing_mode: str = os.getenv("KRUD_BILLING_MODE", "mock")

    # Razorpay — set as secrets in Render / environment; never hard-coded.
    # RAZORPAY_KEY_ID          : Key ID from Razorpay dashboard (Settings → API Keys)
    # RAZORPAY_KEY_SECRET      : Key Secret (keep in Render secret env var)
    # RAZORPAY_WEBHOOK_SECRET  : Webhook secret for HMAC-SHA256 signature verification
    # RAZORPAY_PLAN_ID_BUILDER : Subscription plan ID for Builder plan ($12/month)
    # RAZORPAY_PLAN_ID_PILOT   : Subscription plan ID for Pilot plan ($19/month)
    razorpay_key_id: str | None = os.getenv("RAZORPAY_KEY_ID")
    razorpay_key_secret: str | None = os.getenv("RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: str | None = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    razorpay_plan_id_builder: str = os.getenv("RAZORPAY_PLAN_ID_BUILDER", "")
    razorpay_plan_id_pilot: str = os.getenv("RAZORPAY_PLAN_ID_PILOT", "")

    # ── token budget per plan ─────────────────────────────────────────────────
    # Free    :  40,000 tokens / 5 h  (also used for trialing / past_due)
    # Builder : 500,000 tokens / 5 h  ($12/month)
    # Pilot   : 2,000,000 tokens / 5 h ($19/month)

    billing_success_url: str = os.getenv(
        "KRUD_BILLING_SUCCESS_URL", "http://127.0.0.1:8000/billing/success"
    )
    billing_cancel_url: str = os.getenv(
        "KRUD_BILLING_CANCEL_URL", "http://127.0.0.1:8000/billing/cancel"
    )
    billing_portal_return_url: str = os.getenv(
        "KRUD_BILLING_PORTAL_RETURN_URL", "http://127.0.0.1:8000/billing"
    )

    # ── error tracking ───────────────────────────────────────────────────────
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")

    @property
    def device_base_url(self) -> str:
        """
        URL prefix for device auth pages.

        Precedence:
        1. KRUD_DEVICE_BASE_URL
        2. KRUD_FRONTEND_URL (legacy compatibility)
        3. KRUD_PUBLIC_BASE_URL
        """
        if self.device_base_url_override:
            return self.device_base_url_override.rstrip("/")
        if self.frontend_url:
            return self.frontend_url.rstrip("/")
        return self.public_base_url.rstrip("/")

    # ── CORS — comma-separated list of allowed browser origins ───────────────
    # Default: only the public base URL.  Add more via KRUD_ALLOWED_ORIGINS.
    # Example: KRUD_ALLOWED_ORIGINS=https://dabcloud.in,https://www.dabcloud.in
    allowed_origins_extra: str = os.getenv("KRUD_ALLOWED_ORIGINS", "")

    # ── subscription / auth ───────────────────────────────────────────────────
    trial_days: int = int(os.getenv("KRUD_TRIAL_DAYS", "14"))
    device_code_ttl_seconds: int = int(os.getenv("KRUD_DEVICE_CODE_TTL_SECONDS", "900"))
    device_poll_interval_seconds: int = int(
        os.getenv("KRUD_DEVICE_POLL_INTERVAL_SECONDS", "5")
    )

    # ── session expiry ────────────────────────────────────────────────────────
    # Auth sessions older than this many days are considered expired.
    # Set to 0 to disable expiry (not recommended for production).
    session_ttl_days: int = int(os.getenv("KRUD_SESSION_TTL_DAYS", "90"))

    # ── token budget (Claude Code-style rolling window) ───────────────────────
    # Tokens are counted as prompt_tokens + completion_tokens per LLM call.
    # The window is a rolling 5-hour period, matching Claude Code's behaviour.
    # Limits are per-user; trial users get a tighter cap to control API spend.
    token_budget_window_hours: int = int(os.getenv("KRUD_TOKEN_BUDGET_WINDOW_HOURS", "5"))
    token_budget_free: int = int(os.getenv("KRUD_TOKEN_BUDGET_FREE", "40000"))
    token_budget_builder: int = int(os.getenv("KRUD_TOKEN_BUDGET_BUILDER", "500000"))
    token_budget_pilot: int = int(os.getenv("KRUD_TOKEN_BUDGET_PILOT", "2000000"))
    # Legacy alias — used by existing code paths that pre-date plans
    @property
    def token_budget_trial(self) -> int:
        return self.token_budget_free

    @property
    def token_budget_active(self) -> int:
        return self.token_budget_pilot

    @property
    def razorpay_plan_id(self) -> str:
        """
        Default self-serve plan identifier for billing overview responses.

        Prefer Builder as the entry plan and fall back to Pilot if Builder is
        not configured in the current environment.
        """
        return self.razorpay_plan_id_builder or self.razorpay_plan_id_pilot

    @property
    def allowed_origins(self) -> list[str]:
        """
        Build the final CORS allowed-origins list.

        Always includes public_base_url.  Additional origins are added from
        KRUD_ALLOWED_ORIGINS (comma-separated).
        """
        origins = [self.public_base_url]
        for origin in self.allowed_origins_extra.split(","):
            stripped = origin.strip()
            if stripped:
                origins.append(stripped)
        return origins

    def __repr__(self) -> str:
        """
        Safe representation — secrets are masked so they cannot appear in logs
        or tracebacks (OWASP A09).
        """
        return (
            f"Settings("
            f"api_host={self.api_host!r}, "
            f"public_base_url={self.public_base_url!r}, "
            f"billing_mode={self.billing_mode!r}, "
            f"openai_model={self.openai_model!r}, "
            f"openai_api_key={_mask(self.openai_api_key)}, "
            f"razorpay_key_id={_mask(self.razorpay_key_id)}, "
            f"razorpay_key_secret={_mask(self.razorpay_key_secret)}"
            f")"
        )

    # __str__ delegates to __repr__ so print(settings) is also safe.
    __str__ = __repr__


settings = Settings()
