"""
AI Companion SAAS — Backend API
================================
FastAPI server exposing REST endpoints consumed by the React frontend.

Endpoints
---------
GET  /                          health check
GET  /partners                  list all available AI partner options
POST /sessions                  create a new chat session (choose partner + user profile)
GET  /sessions/{id}             get session metadata
GET  /sessions/{id}/history     get full conversation history
POST /sessions/{id}/chat        send a message & receive AI partner reply
DELETE /sessions/{id}           end / delete a session

Run locally:
    uvicorn main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from google.genai import errors as genai_errors

import session_manager as sm
from partners import PARTNERS
from schemas import (
    ChatMessageRequest,
    ChatResponse,
    CreateSessionRequest,
    DeleteSessionResponse,
    HistoryMessage,
    HistoryResponse,
    PartnerInfo,
    SessionCreatedResponse,
    SessionInfoResponse,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY not set. Add it to your .env file or environment variables."
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI Companion API is up.")
    yield
    print("AI Companion API shutting down.")


app = FastAPI(
    title="AI Companion SAAS",
    description=(
        "Choose your AI companion — virtual girlfriend, boyfriend, or best friend — "
        "and have deeply personal, private conversations powered by Gemini AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — explicit origins required when allow_credentials=True (wildcard is rejected by browsers).
ALLOWED_ORIGINS = [
    "https://ai-partner-ui.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _genai_error_code(exc: genai_errors.APIError) -> int | None:
    """Return an HTTP-like error code from a GenAI SDK exception."""
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    return None


def _map_ai_error_status(exc: genai_errors.APIError) -> int:
    return (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if _genai_error_code(exc) == 429
        else status.HTTP_502_BAD_GATEWAY
    )

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "AI Companion SAAS"}


@app.get("/partners", response_model=list[PartnerInfo], tags=["Partners"])
def list_partners():
    """Return all available AI partner options shown on the selection screen."""
    return [PartnerInfo(**p) for p in PARTNERS.values()]


@app.get("/partners/{partner_id}", response_model=PartnerInfo, tags=["Partners"])
def get_partner(partner_id: str):
    """Get details for a single partner."""
    partner = PARTNERS.get(partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner '{partner_id}' not found.",
        )
    return PartnerInfo(**partner)


@app.post(
    "/sessions",
    response_model=SessionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
def create_session(request: Request, body: CreateSessionRequest):
    """
    Create a new personalised chat session.
    The system prompt is dynamically generated from the user's profile.
    Returns a session_id the frontend must store for subsequent calls.

    Optional headers:
      X-Latitude   — user's GPS latitude
      X-Longitude  — user's GPS longitude
    These are used by the agent's location tool during chat.
    """
    # Extract optional location headers (sent by the frontend after geolocation consent)
    def _parse_coord(header_value: str | None) -> float | None:
        try:
            return float(header_value) if header_value else None
        except (ValueError, TypeError):
            return None

    latitude = _parse_coord(request.headers.get("X-Latitude"))
    longitude = _parse_coord(request.headers.get("X-Longitude"))

    try:
        session = sm.create_session(
            partner_id=body.partner_id,
            user_name=body.user_name,
            nickname=body.nickname,
            user_age=body.user_age,
            language=body.language,
            interests=body.interests,
            personality_pref=body.personality_pref,
            latitude=latitude,
            longitude=longitude,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Trigger the partner to send a natural opening message.
    # This internal prompt is never shown in chat history to the user.
    try:
        opening = sm.send_message(
            session.session_id,
            "[SYSTEM: Start the conversation. Send your very first text to them — "
            "casual, natural, like you just picked up your phone and decided to text. "
            "Don't announce yourself. Don't be overly formal. Just... start talking, "
            "the way you actually would. One to three sentences max.]",
        )
    except genai_errors.ClientError as exc:
        sm.delete_session(session.session_id)
        status_code = _map_ai_error_status(exc)
        raise HTTPException(status_code=status_code, detail=f"AI service error: {exc}")
    except Exception as exc:
        sm.delete_session(session.session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during session start: {exc}",
        )

    return SessionCreatedResponse(
        session_id=session.session_id,
        partner_id=session.partner_id,
        partner_name=session.partner_name,
        user_name=session.user_name,
        language=session.language,
        message=opening,
    )


@app.get("/sessions/{session_id}", response_model=SessionInfoResponse, tags=["Sessions"])
def get_session(session_id: str):
    """Return metadata for an existing session (no message content)."""
    session = sm.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return SessionInfoResponse(**session.to_info())


@app.get(
    "/sessions/{session_id}/history",
    response_model=HistoryResponse,
    tags=["Sessions"],
)
def get_history(session_id: str):
    """Return the full conversation history for a session."""
    try:
        history_raw = sm.get_history(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return HistoryResponse(
        session_id=session_id,
        history=[HistoryMessage(**h) for h in history_raw],
    )


@app.post("/sessions/{session_id}/chat", response_model=ChatResponse, tags=["Chat"])
def chat(session_id: str, body: ChatMessageRequest):
    """
    Send a user message and receive the AI partner's reply.
    The full conversation context is maintained automatically per session.
    """
    session = sm.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    try:
        reply = sm.send_message(session_id, body.message)
    except genai_errors.ClientError as exc:
        status_code = _map_ai_error_status(exc)
        raise HTTPException(status_code=status_code, detail=f"AI service error: {exc}")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI error: {exc}",
        )
    # Refresh session reference for updated count
    session = sm.get_session(session_id)
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        message_count=session.message_count,
    )


@app.delete(
    "/sessions/{session_id}",
    response_model=DeleteSessionResponse,
    tags=["Sessions"],
)
def delete_session(session_id: str):
    """End and permanently delete a session (frontend 'end chat' button)."""
    deleted = sm.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return DeleteSessionResponse(session_id=session_id, deleted=True)
