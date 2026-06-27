from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from fastapi import Request

from .database import connect
from .db import get_settings, now, save_settings


SESSION_COOKIE = "anitrack_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14
PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/me",
    "/api/health",
}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120_000)
    return f"pbkdf2_sha256$120000${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds_text, salt, digest = str(encoded or "").split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_text)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), rounds).hex()
        return hmac.compare_digest(expected, digest)
    except Exception:
        return False


def ensure_auth_defaults() -> None:
    settings = get_settings()
    updates: dict[str, Any] = {}
    if not settings.get("auth_username"):
        updates["auth_username"] = "admin"
    if not settings.get("auth_password_hash"):
        updates["auth_password_hash"] = hash_password("admin")
    if not settings.get("auth_secret"):
        updates["auth_secret"] = secrets.token_urlsafe(32)
    if updates:
        save_settings(updates)


def create_session_token(username: str) -> str:
    settings = get_settings()
    secret = str(settings.get("auth_secret") or "")
    if not secret:
        ensure_auth_defaults()
        secret = str(get_settings().get("auth_secret") or "")
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    body = _b64url(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64url(signature)}"


def verify_session_token(token: str) -> dict[str, Any] | None:
    if "." not in str(token or ""):
        return None
    settings = get_settings()
    secret = str(settings.get("auth_secret") or "")
    if not secret:
        return None
    body, signature = token.split(".", 1)
    expected = _b64url(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp") or 0) < int(time.time()):
        return None
    if str(payload.get("sub") or "") != str(settings.get("auth_username") or "admin"):
        return None
    return payload


def authenticate(username: str, password: str) -> bool:
    settings = get_settings()
    if str(username or "") != str(settings.get("auth_username") or "admin"):
        return False
    return verify_password(password, str(settings.get("auth_password_hash") or ""))


def update_account(username: str, password: str) -> None:
    next_username = str(username or "").strip() or "admin"
    updates: dict[str, Any] = {"auth_username": next_username}
    if str(password or "").strip():
        updates["auth_password_hash"] = hash_password(password.strip())
    save_settings(updates)


def request_user(request: Request) -> dict[str, Any] | None:
    return verify_session_token(request.cookies.get(SESSION_COOKIE, ""))


def is_public_api(path: str) -> bool:
    if path in PUBLIC_API_PATHS:
        return True
    return False


def account_response() -> dict[str, Any]:
    settings = get_settings()
    return {
        "authenticated": True,
        "username": settings.get("auth_username") or "admin",
        "server_time": now(),
    }
