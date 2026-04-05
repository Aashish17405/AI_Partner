"""Database models and session factory for persistent chat storage."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.core.config import DATABASE_URL


def _normalize_db_url(db_url: str) -> str:
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


def _database_enabled(db_url: str) -> bool:
    return bool(db_url and "[YOUR-PASSWORD]" not in db_url)


DATABASE_ENABLED = _database_enabled(DATABASE_URL)
ENGINE = create_engine(_normalize_db_url(DATABASE_URL), pool_pre_ping=True) if DATABASE_ENABLED else None
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, expire_on_commit=False) if ENGINE else None
_db_online = bool(ENGINE)


class Base(DeclarativeBase):
    pass


class ChatSessionRecord(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    partner_id: Mapped[str] = mapped_column(String(40))
    partner_name: Mapped[str] = mapped_column(String(80))
    user_name: Mapped[str] = mapped_column(String(80))
    nickname: Mapped[str] = mapped_column(String(80))
    user_age: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(60), default="English")
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    personality_pref: Mapped[str | None] = mapped_column(String(60), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    messages: Mapped[list["ChatMessageRecord"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ChatMessageRecord(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    session: Mapped[ChatSessionRecord] = relationship(back_populates="messages")


class UserMemoryRecord(Base):
    """Long-term compact facts/memories about a specific user."""
    __tablename__ = "user_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    
    # Simple categorization to help with filtering/scaling
    memory_type: Mapped[str] = mapped_column(String(32), default="fact") 
    
    # The actual compact fact
    content: Mapped[str] = mapped_column(Text)
    
    # 1-5 score, allowing us to prune low-importance memories if context gets too full
    importance: Mapped[int] = mapped_column(Integer, default=1)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


@contextmanager
def db_session() -> Iterator[Session]:
    if not SessionLocal or not _db_online:
        raise RuntimeError("Database is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    global _db_online
    if not ENGINE:
        print("[db] DATABASE_URL missing or placeholder detected; using in-memory fallback.")
        _db_online = False
        return
    try:
        Base.metadata.create_all(bind=ENGINE)
        _db_online = True
        print("[db] PostgreSQL storage enabled.")
    except Exception as exc:
        _db_online = False
        print(f"[db] PostgreSQL init failed ({exc}); using in-memory fallback.")


def is_database_online() -> bool:
    return bool(ENGINE) and _db_online
