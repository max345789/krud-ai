"""
Rate-limiting configuration (OWASP A04: Insecure Design / A05: Misconfiguration).

We use slowapi — a thin Starlette/FastAPI wrapper around the `limits` library.
Limits live in process memory, which is fine for a single-worker deployment
(Render free tier).  To share limits across multiple workers, swap
`Limiter()` for `Limiter(storage_uri="redis://...")`.

Key functions
─────────────
  _real_ip         – extract the true client IP, honouring X-Forwarded-For
                     from Render / Cloudflare.  Only the leftmost address is
                     trusted; subsequent hops can be spoofed by the client.

  user_or_ip_key   – for authenticated endpoints: hash the bearer token so the
                     raw secret never surfaces in rate-limiter storage.
                     Falls back to client IP when no token is present.

Tier defaults (overridable in routes via @limiter.limit("N/period"))
────────────────────────────────────────────────────────────────────
  STRICT   –  5/minute   unauthenticated write flows (device form, mock billing)
  AUTH     – 10/minute   device start / complete
  POLL     – 120/minute  device poll (CLI polls every 5 s; allow generous headroom)
  STANDARD – 30/minute   authenticated user actions (chat, billing portal)
  RELAXED  – 60/minute   cheap reads (account info)
  PUBLIC   – 20/minute   unauthenticated reads (releases, health)
"""
from __future__ import annotations

import hashlib

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _real_ip(request: Request) -> str:
    """
    Return the originating client IP.

    Render and Cloudflare prepend the real IP as the first value in
    X-Forwarded-For.  We never trust values after the first comma because
    those can be injected by the client (OWASP A05).
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Direct connection (local dev / no proxy).
    return get_remote_address(request)


def user_or_ip_key(request: Request) -> str:
    """
    Rate-limit authenticated requests per-user, unauthenticated per-IP.

    The bearer token is SHA-256 hashed before use as a cache key so the raw
    credential is never written to memory/logs.  We use the first 32 hex
    chars of the digest — that's 128 bits, more than enough for uniqueness.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        raw = auth[7:].strip()
        digest = hashlib.sha256(raw.encode()).hexdigest()[:32]
        return f"user:{digest}"
    return f"ip:{_real_ip(request)}"


# Global limiter instance.
# The default key_func governs IP-keyed (unauthenticated) endpoints.
# Authenticated endpoints pass key_func=user_or_ip_key in their decorator.
limiter = Limiter(key_func=_real_ip)
