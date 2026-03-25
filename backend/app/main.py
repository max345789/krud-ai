"""
FastAPI application entry point.

Security hardening applied here
────────────────────────────────
1. CORS (OWASP A05: Misconfiguration)
   - Origins restricted to the configured public URL plus any extras from
     KRUD_ALLOWED_ORIGINS env var.  The previous allow_origins=["*"] with
     allow_credentials=True was both invalid per the CORS spec and overly
     permissive.
   - Methods restricted to GET and POST (the only verbs used by this API).
   - Headers restricted to the two the API actually requires.

2. Rate limiting (OWASP A04: Insecure Design)
   - slowapi Limiter instance registered on app.state so route decorators in
     routes.py can reference it via request.app.state.limiter.
   - Custom 429 handler returns structured JSON instead of the default HTML
     response; includes a Retry-After hint.

3. Security response headers (OWASP A05: Misconfiguration)
   - X-Content-Type-Options: nosniff  — prevents MIME sniffing attacks.
   - X-Frame-Options: DENY            — blocks clickjacking.
   - Referrer-Policy                  — limits referrer leakage.
   - Cache-Control: no-store          — prevents sensitive API responses from
                                        being cached by proxies or browsers.
     (HTML pages served by /device and /billing/* override this where needed.)
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.db import Database
from app.core.limiter import limiter

# ── database init ─────────────────────────────────────────────────────────────

db = Database()
db.initialize()

# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Krud AI Control Plane",
    version="0.1.0",
    # Disable the automatic /docs and /redoc endpoints in production to avoid
    # leaking internal API shape.  Set KRUD_DOCS_ENABLED=1 locally if needed.
    docs_url="/docs" if os.getenv("KRUD_DOCS_ENABLED") else None,
    redoc_url="/redoc" if os.getenv("KRUD_DOCS_ENABLED") else None,
    openapi_url="/openapi.json" if os.getenv("KRUD_DOCS_ENABLED") else None,
)

# ── rate limiter ──────────────────────────────────────────────────────────────

# Register the limiter on app.state so route decorators in routes.py can
# reference it via request.app.state.limiter.
app.state.limiter = limiter

# Add the SlowAPI middleware (injects rate-limit headers into responses).
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Return a clean JSON 429 instead of slowapi's default plain-text response.
    Retry-After is set to 60 seconds as a safe default when not available.
    """
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please wait before retrying.",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# ── CORS ──────────────────────────────────────────────────────────────────────
# allow_origins must NOT be ["*"] when allow_credentials=True — browsers reject
# that combination (CORS spec).  We use the explicit origin list from config.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── security headers middleware ───────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Attach security headers to every response (OWASP A05: Misconfiguration).

    These headers are low-risk and safe to apply globally:
    - nosniff    : Prevents browsers from MIME-sniffing away from declared Content-Type.
    - DENY frame : Blocks this API from being embedded in an iframe (clickjacking).
    - Referrer   : Limits how much of the URL is sent to third parties.
    - no-store   : Prevents proxies/browsers from caching API responses that may
                   contain tokens or sensitive account data.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Only set Cache-Control on API (JSON) responses; HTML billing/device pages
    # have their own caching semantics.
    if "text/html" not in response.headers.get("content-type", ""):
        response.headers["Cache-Control"] = "no-store"
    return response


# ── routes ────────────────────────────────────────────────────────────────────

app.include_router(router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
