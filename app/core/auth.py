"""Supabase token verification helpers."""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import SUPABASE_ANON_KEY, SUPABASE_JWT_AUDIENCE, SUPABASE_JWT_SECRET, SUPABASE_URL


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


def _fetch_user_from_supabase_fallback(token: str) -> dict:
    """Fallback to Supabase API if local verification secret is missing."""
    req = urllib.request.Request(
        url=f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:  # noqa: S310
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "403" in msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Supabase session (API check failed).",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase auth validation currently unavailable: {exc}",
        ) from exc


def get_current_user(request: Request) -> AuthUser:
    token = _extract_bearer_token(request)

    # 1. Try local verification FIRST (Zero latency, no rate limits)
    if SUPABASE_JWT_SECRET:
        try:
            # Supabase JWT Secret is often Base64-encoded. We decode it if needed.
            secret = SUPABASE_JWT_SECRET
            if "==" in secret or len(secret) > 40:
                try:
                    secret = base64.b64decode(secret)
                except Exception:
                    # Fallback to literal if decoding fails
                    pass

            # Expanded algorithm list to avoid "alg not allowed" errors
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256", "HS384", "HS512"],
                audience=SUPABASE_JWT_AUDIENCE,
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing subject (user id).",
                )
            return AuthUser(id=str(user_id), email=str(email) if email else None)
        except JWTError:
            # Fallback for algorithm mismatch (ES256, RS256, etc.) or Signature verification failure.
            # Local verification is for speed (HS256 only). If it fails, let's ask Supabase directly via API.
            pass
            
            # 1.5 Fallback to API check
            user = _fetch_user_from_supabase_fallback(token)
            user_id = user.get("id")
            email = user.get("email")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired credentials (failed local and remote verification).",
                )
            return AuthUser(id=str(user_id), email=str(email) if email else None)

    # 2. Fallback to HTTP request if no secret is configured
    user = _fetch_user_from_supabase_fallback(token)
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase returned no user id.",
        )
    return AuthUser(id=str(user_id), email=user.get("email"))

