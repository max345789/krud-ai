"""
Input sanitization and validation helpers (OWASP A03: Injection).

These functions are the single source of truth for every constraint applied to
user-supplied data.  They are used in two places:

  1. Pydantic @field_validator methods in schemas.py  (JSON body fields)
  2. FastAPI query/form parameter coercion in routes.py

Design rules
────────────
- Reject first, explain clearly.  Never silently truncate or modify input in a
  way the caller would not expect.
- All validators return the cleaned value so they can be chained.
- Functions that raise HTTPException are intended for use in route handlers
  (query params); functions that raise ValueError are for Pydantic validators.
"""
from __future__ import annotations

import re

from fastapi import HTTPException, status

# ── constants ────────────────────────────────────────────────────────────────

# The only values that may ever be written to users.subscription_status.
ALLOWED_SUBSCRIPTION_STATUSES: frozenset[str] = frozenset(
    {"trialing", "active", "past_due", "canceled"}
)

# user_code format: exactly XXXX-XXXX (uppercase ASCII letters and digits).
_USER_CODE_RE = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$")

# device_code: URL-safe base64 alphabet, 20–64 chars (matches secrets.token_urlsafe(24)).
_DEVICE_CODE_RE = re.compile(r"^[A-Za-z0-9_\-]{20,64}$")

# client_name: printable ASCII letters, digits, hyphens, dots, spaces.
_CLIENT_NAME_RE = re.compile(r"^[\w\-. ]{2,64}$")

# Minimal structural email check for query-param coercion.
# Pydantic EmailStr handles the full RFC check for JSON body fields.
_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{1,63}$")

# Path safety: reject null bytes and ASCII control characters (0x00–0x1F, 0x7F).
_SAFE_PATH_RE = re.compile(r"^[^\x00-\x1f\x7f]+$")

# Release channel allowlist.
_ALLOWED_CHANNELS: frozenset[str] = frozenset({"stable", "beta"})


# ── Pydantic field validators (raise ValueError) ──────────────────────────────

def validate_no_null_bytes(value: str) -> str:
    """Reject any string containing a null byte (OWASP A03 — injection defence)."""
    if "\x00" in value:
        raise ValueError("Null bytes are not permitted")
    return value.strip()


def validate_device_code(value: str) -> str:
    """
    Ensure device_code matches the URL-safe base64 pattern produced by
    secrets.token_urlsafe(24).  Rejects garbage that would waste a DB lookup.
    """
    v = value.strip()
    if not _DEVICE_CODE_RE.match(v):
        raise ValueError("Invalid device_code format")
    return v


def validate_user_code(value: str) -> str:
    """Normalise to uppercase and check XXXX-XXXX pattern."""
    v = value.strip().upper()
    if not _USER_CODE_RE.match(v):
        raise ValueError("user_code must be in the format XXXX-XXXX")
    return v


def validate_client_name(value: str) -> str:
    """Allow printable safe chars only; prevents log injection via client_name."""
    v = value.strip()
    if not _CLIENT_NAME_RE.match(v):
        raise ValueError(
            "client_name may only contain letters, digits, hyphens, dots, and spaces"
        )
    return v


def validate_cwd(value: str | None) -> str | None:
    """
    Reject cwd values containing ASCII control characters.

    The cwd string is forwarded to the LLM as contextual metadata.  Control
    characters could be used to inject fake system-prompt content (prompt
    injection via newlines/escape sequences).
    """
    if value is None:
        return None
    if not _SAFE_PATH_RE.match(value):
        raise ValueError("cwd contains invalid control characters")
    return value.strip()


def validate_subscription_status(value: str) -> str:
    """
    Allow only the four canonical subscription states.

    Prevents arbitrary strings from reaching the subscription_status column,
    which is read back in auth and billing logic.
    """
    v = value.strip().lower()
    if v not in ALLOWED_SUBSCRIPTION_STATUSES:
        raise ValueError(
            f"status must be one of: {', '.join(sorted(ALLOWED_SUBSCRIPTION_STATUSES))}"
        )
    return v


# ── FastAPI query/form param guards (raise HTTPException) ─────────────────────

def require_valid_email(email: str) -> str:
    """
    Light structural email check for query/form parameters.

    Routes that receive email as a query param cannot use Pydantic EmailStr
    directly.  This covers the obvious cases; Pydantic handles RFC-5322
    compliance for JSON body fields.
    """
    v = email.strip().lower()
    if len(v) > 254 or not _EMAIL_RE.match(v):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address",
        )
    return v


def require_valid_user_code(user_code: str) -> str:
    """HTTP-layer guard for user_code query/form params."""
    try:
        return validate_user_code(user_code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def require_valid_subscription_status(status_value: str) -> str:
    """HTTP-layer guard for subscription status form fields."""
    try:
        return validate_subscription_status(status_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def require_valid_channel(channel: str) -> str:
    """Only 'stable' and 'beta' are valid release channels."""
    v = channel.strip().lower()
    if v not in _ALLOWED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"channel must be one of: {', '.join(sorted(_ALLOWED_CHANNELS))}",
        )
    return v
