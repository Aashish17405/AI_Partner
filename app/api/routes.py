"""HTTP route definitions for the AI Companion API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import AuthUser, get_current_user
from app.domain.partners import PARTNERS
from app.schemas import (
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
from app.services import session_manager as sm

router = APIRouter()


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "429" in msg
        or "rate limit" in msg
        or "rate_limit" in msg
        or "quota" in msg
        or "too many requests" in msg
    )


def _map_ai_error_status(exc: Exception) -> int:
    return (
        status.HTTP_429_TOO_MANY_REQUESTS
        if _is_rate_limit_error(exc)
        else status.HTTP_502_BAD_GATEWAY
    )


def _fallback_opening(partner_name: str, user_name: str) -> str:
    return (
        f"Hey {user_name}, it's {partner_name}. I might be a bit delayed right now, "
        "but I'm here with you. Tell me what's on your mind."
    )


@router.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "AI Companion SAAS"}


@router.get("/partners", response_model=list[PartnerInfo], tags=["Partners"])
def list_partners():
    return [PartnerInfo(**p) for p in PARTNERS.values()]


@router.get("/partners/{partner_id}", response_model=PartnerInfo, tags=["Partners"])
def get_partner(partner_id: str):
    partner = PARTNERS.get(partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner '{partner_id}' not found.",
        )
    return PartnerInfo(**partner)


@router.post(
    "/sessions",
    response_model=SessionCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
def create_session(
    request: Request,
    body: CreateSessionRequest,
    user: AuthUser = Depends(get_current_user),
):
    def _parse_coord(header_value: str | None) -> float | None:
        try:
            return float(header_value) if header_value else None
        except (ValueError, TypeError):
            return None

    latitude = _parse_coord(request.headers.get("X-Latitude"))
    longitude = _parse_coord(request.headers.get("X-Longitude"))

    try:
        session = sm.create_session(
            user_id=user.id,
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

    opening = _fallback_opening(session.partner_name, session.user_name)
    try:
        opening = sm.send_message(
            session.session_id,
            "[SYSTEM: Start the conversation. Send your very first text to them - "
            "casual, natural, like you just picked up your phone and decided to text. "
            "Do not announce yourself. Do not be overly formal. Just start talking "
            "the way you actually would. One to three sentences max.]",
            user.id,
        )
    except Exception as exc:
        print(f"[sessions.create] AI opening fallback used: {exc}")

    return SessionCreatedResponse(
        session_id=session.session_id,
        partner_id=session.partner_id,
        partner_name=session.partner_name,
        user_name=session.user_name,
        language=session.language,
        message=opening,
    )


@router.get("/sessions", response_model=list[SessionInfoResponse], tags=["Sessions"])
def list_sessions(user: AuthUser = Depends(get_current_user)):
    sessions = sm.list_sessions(user.id)
    return [SessionInfoResponse(**session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=SessionInfoResponse, tags=["Sessions"])
def get_session(
    session_id: str,
    user: AuthUser = Depends(get_current_user),
):
    session = sm.get_session(session_id, user_id=user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return SessionInfoResponse(**session.to_info())


@router.get(
    "/sessions/{session_id}/history",
    response_model=HistoryResponse,
    tags=["Sessions"],
)
def get_history(
    session_id: str,
    user: AuthUser = Depends(get_current_user),
):
    try:
        history_raw = sm.get_history(session_id, user_id=user.id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return HistoryResponse(
        session_id=session_id,
        history=[HistoryMessage(**h) for h in history_raw],
    )


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse, tags=["Chat"])
def chat(
    session_id: str,
    body: ChatMessageRequest,
    user: AuthUser = Depends(get_current_user),
):
    session = sm.get_session(session_id, user_id=user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    try:
        reply = sm.send_message(session_id, body.message, user_id=user.id)
    except Exception as exc:
        status_code = _map_ai_error_status(exc)
        raise HTTPException(status_code=status_code, detail=f"AI service error: {exc}")

    session = sm.get_session(session_id, user_id=user.id)
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        message_count=session.message_count,
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteSessionResponse,
    tags=["Sessions"],
)
def delete_session(
    session_id: str,
    user: AuthUser = Depends(get_current_user),
):
    deleted = sm.delete_session(session_id, user_id=user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return DeleteSessionResponse(session_id=session_id, deleted=True)
