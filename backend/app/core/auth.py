from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from fastapi import Header, HTTPException, status

from app.core.db import Database

db = Database()

_PASSWORD_SCHEME = "scrypt"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith("krud_") or len(token) > 256:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    return token


def issue_session_token() -> str:
    return f"krud_{secrets.token_urlsafe(32)}"


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    derived_b64 = base64.urlsafe_b64encode(derived).decode("ascii")
    return (
        f"{_PASSWORD_SCHEME}$n={_SCRYPT_N},r={_SCRYPT_R},p={_SCRYPT_P}"
        f"${salt_b64}${derived_b64}"
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        scheme, params, salt_b64, expected_b64 = stored_hash.split("$", 3)
        if scheme != _PASSWORD_SCHEME:
            return False
        parsed = {
            key: int(value)
            for key, value in (
                item.split("=", 1) for item in params.split(",") if "=" in item
            )
        }
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_b64.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=parsed.get("n", _SCRYPT_N),
            r=parsed.get("r", _SCRYPT_R),
            p=parsed.get("p", _SCRYPT_P),
            dklen=len(expected),
        )
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)


def get_current_user(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    user = db.get_user_by_session_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    return user
