"""Supabase token verification helpers."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.core.config import SUPABASE_ANON_KEY, SUPABASE_URL


@dataclass
class AuthUser:
    id: str
    email: str | None = None


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token.",
        )
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token.",
        )
    return token


def _fetch_user_from_supabase(token: str) -> dict:
    req = urllib.request.Request(
        url=f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=8) as response:  # noqa: S310
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def get_current_user(request: Request) -> AuthUser:
    token = _extract_bearer_token(request)

    try:
        user = _fetch_user_from_supabase(token)
    except Exception as exc:
        message = str(exc)
        if "401" in message or "403" in message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase auth validation failed: {exc}",
        )

    user_id = user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no user id.",
        )
    email = user.get("email")
    return AuthUser(id=str(user_id), email=str(email) if email else None)
