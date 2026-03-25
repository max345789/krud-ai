from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv("KRUD_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("KRUD_API_PORT", "8000"))
    public_base_url: str = os.getenv("KRUD_PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    download_base_url: str = os.getenv("KRUD_DOWNLOAD_BASE_URL", "https://downloads.krud.ai")
    release_version: str = os.getenv("KRUD_RELEASE_VERSION", "0.1.0")
    database_path: Path = Path(os.getenv("KRUD_DATABASE_PATH", "krud.db"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    billing_mode: str = os.getenv("KRUD_BILLING_MODE", "mock")
    stripe_price_id: str = os.getenv("KRUD_STRIPE_PRICE_ID", "price_krud_monthly")
    stripe_secret_key: str | None = os.getenv("STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = os.getenv("STRIPE_WEBHOOK_SECRET")
    billing_success_url: str = os.getenv("KRUD_BILLING_SUCCESS_URL", "http://127.0.0.1:8000/billing/success")
    billing_cancel_url: str = os.getenv("KRUD_BILLING_CANCEL_URL", "http://127.0.0.1:8000/billing/cancel")
    billing_portal_return_url: str = os.getenv("KRUD_BILLING_PORTAL_RETURN_URL", "http://127.0.0.1:8000/billing")
    trial_days: int = int(os.getenv("KRUD_TRIAL_DAYS", "14"))
    device_code_ttl_seconds: int = int(os.getenv("KRUD_DEVICE_CODE_TTL_SECONDS", "900"))
    device_poll_interval_seconds: int = int(os.getenv("KRUD_DEVICE_POLL_INTERVAL_SECONDS", "5"))


settings = Settings()
