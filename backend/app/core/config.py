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
  STRIPE_SECRET_KEY        – required for real billing; if absent, mock billing is used
  STRIPE_WEBHOOK_SECRET    – required to verify Stripe webhook signatures
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
    # ── frontend URL (landing page) — used for device auth redirect ──────────
    frontend_url: str = os.getenv("KRUD_FRONTEND_URL", "")

    # ── release distribution ─────────────────────────────────────────────────
    download_base_url: str = os.getenv("KRUD_DOWNLOAD_BASE_URL", "https://downloads.krud.ai")
    release_version: str = os.getenv("KRUD_RELEASE_VERSION", "0.1.0")

    # ── database ─────────────────────────────────────────────────────────────
    # PostgreSQL connection string (Supabase).  Required in production.
    # Example: postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    database_url: str = os.getenv("DATABASE_URL", "")

    # ── LLM — key is read from env only, never hard-coded ────────────────────
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))

    # ── billing — keys are read from env only, never hard-coded ─────────────
    # billing_mode: "mock" (local dev, no real payments) or "dodo" (production)
    billing_mode: str = os.getenv("KRUD_BILLING_MODE", "mock")

    # Dodo Payments — set as secrets in Render / environment; never hard-coded.
    # DODO_PAYMENTS_API_KEY  : live or test API key from the Dodo dashboard
    # DODO_PAYMENTS_WEBHOOK_KEY : webhook signing secret for signature verification
    # DODO_PAYMENTS_PRODUCT_ID  : the product/plan ID to attach to new subscriptions
    # DODO_PAYMENTS_ENVIRONMENT : "test_mode" (sandbox) or "live_mode" (production)
    dodo_api_key: str | None = os.getenv("DODO_PAYMENTS_API_KEY")
    dodo_webhook_key: str | None = os.getenv("DODO_PAYMENTS_WEBHOOK_KEY")
    dodo_product_id: str = os.getenv("DODO_PAYMENTS_PRODUCT_ID", "")
    dodo_environment: str = os.getenv("DODO_PAYMENTS_ENVIRONMENT", "test_mode")

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
        """URL prefix for device auth pages — frontend if set, else backend."""
        return self.frontend_url.rstrip("/") if self.frontend_url else self.public_base_url

    # ── CORS — comma-separated list of allowed browser origins ───────────────
    # Default: only the public base URL.  Add more via KRUD_ALLOWED_ORIGINS.
    # Example: KRUD_ALLOWED_ORIGINS=https://app.krud.ai,https://staging.krud.ai
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
    token_budget_trial: int = int(os.getenv("KRUD_TOKEN_BUDGET_TRIAL", "40000"))
    token_budget_active: int = int(os.getenv("KRUD_TOKEN_BUDGET_ACTIVE", "2000000"))

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
            f"dodo_environment={self.dodo_environment!r}, "
            f"openai_model={self.openai_model!r}, "
            f"openai_api_key={_mask(self.openai_api_key)}, "
            f"dodo_api_key={_mask(self.dodo_api_key)}, "
            f"dodo_webhook_key={_mask(self.dodo_webhook_key)}"
            f")"
        )

    # __str__ delegates to __repr__ so print(settings) is also safe.
    __str__ = __repr__


settings = Settings()
