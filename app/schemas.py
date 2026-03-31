"""
Pydantic request/response models for the API.
These are the contracts that the React frontend will talk to.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    partner_id: str = Field(
        ...,
        description="One of: 'girlfriend', 'boyfriend', 'bestfriend'",
        examples=["girlfriend"],
    )
    user_name: str = Field(..., min_length=1, max_length=50, examples=["Aashish"])
    nickname: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=30,
        description="What the AI partner should call the user (pet name / nickname). Falls back to user_name if not set.",
        examples=["Ash", "babe", "Ashu"],
    )
    user_age: int = Field(..., ge=18, le=100, description="Must be 18+")
    language: str = Field(
        default="English",
        description="Preferred conversation language",
        examples=["English", "Hindi", "Telugu"],
    )
    interests: Optional[list[str]] = Field(
        default=None,
        description="List of hobbies/interests to make conversation personal",
        examples=[["cricket", "movies", "coding"]],
    )
    personality_pref: Optional[str] = Field(
        default=None,
        description="Preferred personality flavour e.g. 'funny', 'serious', 'caring'",
        examples=["funny"],
    )


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, examples=["Hey, how was your day?"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class PartnerInfo(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    avatar_hint: str
    languages_supported: list[str]


class SessionCreatedResponse(BaseModel):
    session_id: str
    partner_id: str
    partner_name: str
    user_name: str
    language: str
    message: str  # welcome message from the AI partner


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    message_count: int


class SessionInfoResponse(BaseModel):
    session_id: str
    partner_id: str
    partner_name: str
    user_name: str
    nickname: Optional[str]
    language: str
    interests: list[str]
    personality_pref: Optional[str]
    created_at: str
    last_active: str
    message_count: int


class HistoryMessage(BaseModel):
    role: str   # "user" or "model"
    text: str


class HistoryResponse(BaseModel):
    session_id: str
    history: list[HistoryMessage]


class DeleteSessionResponse(BaseModel):
    session_id: str
    deleted: bool


class ErrorResponse(BaseModel):
    detail: str
