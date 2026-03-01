"""
In-memory session store.

Each session holds:
 - The Gemini ChatSession object (maintains full conversation history natively)
 - Metadata: partner_id, user profile, timestamps

For production you'd replace the in-memory dict with Redis / a DB,
but this is the perfect starting point before attaching a frontend.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from google import genai
from google.genai import types

from partners import PARTNERS, get_system_prompt


# Gemini model name used across all sessions
GEMINI_MODEL = "gemini-2.5-flash"

# { session_id: SessionData }
_sessions: dict[str, "SessionData"] = {}


class SessionData:
    def __init__(
        self,
        session_id: str,
        partner_id: str,
        user_name: str,
        nickname: Optional[str],
        user_age: int,
        language: str,
        interests: list[str],
        personality_pref: Optional[str],
        genai_client,  # google.genai.Client — kept alive to prevent httpx closure
        chat,  # google.genai.chats.Chat
    ):
        self.session_id = session_id
        self.partner_id = partner_id
        self.partner_name = PARTNERS[partner_id]["name"]
        self.user_name = user_name
        self.nickname = nickname or user_name  # fallback to real name if no nickname set
        self.user_age = user_age
        self.language = language
        self.interests = interests
        self.personality_pref = personality_pref
        self.genai_client = genai_client  # hold a strong reference so httpx stays open
        self.chat = chat
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_active = self.created_at
        self.message_count = 0

    def to_info(self) -> dict:
        """Serialisable session metadata (no internal chat object)."""
        return {
            "session_id": self.session_id,
            "partner_id": self.partner_id,
            "partner_name": self.partner_name,
            "user_name": self.user_name,
            "nickname": self.nickname,
            "language": self.language,
            "interests": self.interests,
            "personality_pref": self.personality_pref,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "message_count": self.message_count,
        }


def create_session(
    api_key: str,
    partner_id: str,
    user_name: str,
    nickname: Optional[str] = None,
    user_age: int = 22,
    language: str = "English",
    interests: Optional[list[str]] = None,
    personality_pref: Optional[str] = None,
) -> SessionData:
    """Create a new Gemini chat session personalised for the user."""

    if partner_id not in PARTNERS:
        raise ValueError(f"Partner '{partner_id}' does not exist.")

    interests = interests or []
    resolved_nickname = nickname or user_name

    system_prompt = get_system_prompt(
        partner_id=partner_id,
        user_name=user_name,
        nickname=resolved_nickname,
        user_age=user_age,
        language=language,
        interests=interests,
        personality_pref=personality_pref,
    )

    # Google Search grounding tool — lets every agent look up live information
    # (current events, facts, news) during the conversation when needed.
    search_tool = types.Tool(google_search=types.GoogleSearch())

    client = genai.Client(api_key=api_key)
    chat = client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[search_tool],
        ),
    )

    session_id = str(uuid.uuid4())
    session = SessionData(
        session_id=session_id,
        partner_id=partner_id,
        user_name=user_name,
        nickname=resolved_nickname,
        user_age=user_age,
        language=language,
        interests=interests,
        personality_pref=personality_pref,
        genai_client=client,  # keep alive
        chat=chat,
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[SessionData]:
    return _sessions.get(session_id)


def send_message(session_id: str, message: str) -> str:
    """Send a user message and return the AI partner's reply."""
    session = get_session(session_id)
    if not session:
        raise KeyError(f"Session '{session_id}' not found.")

    response = session.chat.send_message(message)
    session.message_count += 1
    session.last_active = datetime.now(timezone.utc).isoformat()
    return response.text


def get_history(session_id: str) -> list[dict]:
    """Return the full conversation history for a session."""
    session = get_session(session_id)
    if not session:
        raise KeyError(f"Session '{session_id}' not found.")

    history = []
    for turn in session.chat.get_history():
        text = ""
        if turn.parts:
            text = "".join(
                part.text for part in turn.parts if hasattr(part, "text") and part.text
            )
        history.append({"role": turn.role, "text": text})
    return history


def delete_session(session_id: str) -> bool:
    """Remove a session from the store."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def list_sessions() -> list[dict]:
    """Dev/admin helper — returns metadata for all active sessions."""
    return [s.to_info() for s in _sessions.values()]
