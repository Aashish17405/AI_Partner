"""
Hybrid session store — Redis in production (Vercel), in-memory locally.

Vercel runs serverless functions: each request may start a fresh Python
process, so a global dict would lose sessions between calls.
Upstash Redis is used instead — it's HTTP-based (no persistent TCP socket),
free-tier, and the official Vercel partner for KV storage.

Local development falls back to an in-memory dict automatically when the
UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN env vars are absent.

Session data stored per key  aiptnr:session:{session_id}  in Redis as JSON.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from google import genai
from google.genai import errors as genai_errors, types

from partners import PARTNERS, get_system_prompt
from tools import AGENT_TOOLS, dispatch_tool_call

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_ENABLE_TOOLS = os.getenv("GEMINI_ENABLE_TOOLS", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SESSION_TTL = 60 * 60 * 24 * 7   # 7 days (seconds in Redis)


# ---------------------------------------------------------------------------
# Storage backend — pick Redis or in-memory at import time
# ---------------------------------------------------------------------------

def _make_redis():
    url   = os.getenv("UPSTASH_REDIS_REST_URL", "")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis   # type: ignore[import]
        print("[session_manager] Using Upstash Redis for session storage.")
        return Redis(url=url, token=token)
    except ImportError:
        print("[session_manager] upstash-redis not installed; falling back to in-memory.")
        return None


_redis = _make_redis()
_local: dict[str, dict] = {}   # fallback in-memory store


def _key(session_id: str) -> str:
    return f"aiptnr:session:{session_id}"


def _save(data: dict) -> None:
    if _redis:
        _redis.setex(_key(data["session_id"]), SESSION_TTL, json.dumps(data))
    else:
        _local[data["session_id"]] = data


def _load(session_id: str) -> Optional[dict]:
    if _redis:
        raw = _redis.get(_key(session_id))
        return json.loads(raw) if raw else None
    return _local.get(session_id)


def _remove(session_id: str) -> bool:
    if _redis:
        return bool(_redis.delete(_key(session_id)))
    if session_id in _local:
        del _local[session_id]
        return True
    return False


# ---------------------------------------------------------------------------
# SessionData — thin view over the stored dict (keeps API compatibility)
# ---------------------------------------------------------------------------

class SessionData:
    def __init__(self, data: dict):
        self._d = data

    @property
    def session_id(self)       -> str:            return self._d["session_id"]
    @property
    def partner_id(self)       -> str:            return self._d["partner_id"]
    @property
    def partner_name(self)     -> str:            return self._d["partner_name"]
    @property
    def user_name(self)        -> str:            return self._d["user_name"]
    @property
    def nickname(self)         -> str:            return self._d.get("nickname", self._d["user_name"])
    @property
    def user_age(self)         -> int:            return self._d["user_age"]
    @property
    def language(self)         -> str:            return self._d["language"]
    @property
    def interests(self)        -> list:           return self._d.get("interests", [])
    @property
    def personality_pref(self) -> Optional[str]:  return self._d.get("personality_pref")
    @property
    def created_at(self)       -> str:            return self._d["created_at"]
    @property
    def last_active(self)      -> str:            return self._d["last_active"]
    @property
    def message_count(self)    -> int:            return self._d["message_count"]
    @property
    def latitude(self)         -> Optional[float]: return self._d.get("latitude")
    @property
    def longitude(self)        -> Optional[float]: return self._d.get("longitude")

    def to_info(self) -> dict:
        """Return serialisable metadata (no history)."""
        return {k: v for k, v in self._d.items() if k != "history"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_session(
    partner_id: str,
    user_name: str,
    nickname: Optional[str] = None,
    user_age: int = 22,
    language: str = "English",
    interests: Optional[list[str]] = None,
    personality_pref: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    api_key: Optional[str] = None,   # kept for backward compat; ignored
) -> SessionData:
    """Create a new chat session and persist it to the store."""
    if partner_id not in PARTNERS:
        raise ValueError(f"Partner '{partner_id}' does not exist.")

    now = datetime.now(timezone.utc).isoformat()
    data: dict = {
        "session_id":       str(uuid.uuid4()),
        "partner_id":       partner_id,
        "partner_name":     PARTNERS[partner_id]["name"],
        "user_name":        user_name,
        "nickname":         nickname or user_name,
        "user_age":         user_age,
        "language":         language,
        "interests":        interests or [],
        "personality_pref": personality_pref,
        "latitude":         latitude,
        "longitude":        longitude,
        "created_at":       now,
        "last_active":      now,
        "message_count":    0,
        "history":          [],
    }
    _save(data)
    return SessionData(data)


def get_session(session_id: str) -> Optional[SessionData]:
    data = _load(session_id)
    return SessionData(data) if data else None


def _extract_function_calls(response) -> list:
    calls = []
    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in content.parts or []:
            function_call = getattr(part, "function_call", None)
            if function_call:
                calls.append(function_call)
    return calls


def _extract_response_text(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        parts = content.parts or []
        chunks = [part.text for part in parts if getattr(part, "text", None)]
        if chunks:
            return "".join(chunks).strip()
    return ""


def _tool_mode_unsupported(exc: genai_errors.ClientError) -> bool:
    if getattr(exc, "code", None) != 400:
        return False
    message = (getattr(exc, "message", "") or str(exc)).lower()
    return (
        "tool use with function calling is unsupported by the model" in message
        or ("function calling is unsupported" in message and "model" in message)
        or ("tools are not supported" in message and "model" in message)
    )


def send_message(session_id: str, message: str) -> str:
    """
    Send a user message and return the AI partner reply.

    On every call:
      1. Load session data + conversation history from the store.
      2. Rebuild a fresh Gemini ChatSession seeded with that history
         (stateless — safe for serverless / Vercel).
      3. Run the agentic tool-call loop (datetime / location / search).
      4. Persist the updated history back to the store.
    """
    data = _load(session_id)
    if not data:
        raise KeyError(f"Session '{session_id}' not found.")

    api_key = os.getenv("GEMINI_API_KEY", "")

    system_prompt = get_system_prompt(
        partner_id=data["partner_id"],
        user_name=data["user_name"],
        nickname=data.get("nickname", data["user_name"]),
        user_age=data["user_age"],
        language=data["language"],
        interests=data.get("interests", []),
        personality_pref=data.get("personality_pref"),
    )

    # Reconstruct Gemini-format history from stored plain-text turns
    genai_history = [
        types.Content(
            role=msg["role"],
            parts=[types.Part.from_text(text=msg["text"])],
        )
        for msg in data.get("history", [])
        if msg.get("text")
    ]

    client = genai.Client(api_key=api_key)
    tools_active = GEMINI_ENABLE_TOOLS

    try:
        config_kwargs = {"system_instruction": system_prompt}
        if tools_active:
            config_kwargs["tools"] = AGENT_TOOLS
        chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(**config_kwargs),
            history=genai_history,
        )
        response = chat.send_message(message)
    except genai_errors.ClientError as exc:
        if not tools_active or not _tool_mode_unsupported(exc):
            raise
        # Fallback for models that reject tool/function mode.
        tools_active = False
        chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
            history=genai_history,
        )
        response = chat.send_message(message)

    # Agentic tool-call loop (max 5 rounds)
    if tools_active:
        for _ in range(5):
            function_calls = _extract_function_calls(response)
            if not function_calls:
                break

            tool_result_parts = []
            for fc in function_calls:
                result = dispatch_tool_call(
                    fc.name,
                    dict(fc.args) if fc.args else {},
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                )
                tool_result_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )
            response = chat.send_message(tool_result_parts)

    reply_text = _extract_response_text(response)
    if not reply_text:
        raise RuntimeError("Model returned an empty reply.")

    # Persist new turns + updated metadata
    data["history"].append({"role": "user",  "text": message})
    data["history"].append({"role": "model", "text": reply_text})
    data["message_count"] += 1
    data["last_active"] = datetime.now(timezone.utc).isoformat()
    _save(data)

    return reply_text


def get_history(session_id: str) -> list[dict]:
    """Return the full conversation history for a session."""
    data = _load(session_id)
    if data is None:
        raise KeyError(f"Session '{session_id}' not found.")
    return data.get("history", [])


def delete_session(session_id: str) -> bool:
    """Remove a session from the store."""
    return _remove(session_id)


def list_sessions() -> list[dict]:
    """Dev helper — only works with the in-memory fallback."""
    if _redis:
        return []   # scanning all Redis keys is expensive; skip in prod
    return [SessionData(d).to_info() for d in _local.values()]
