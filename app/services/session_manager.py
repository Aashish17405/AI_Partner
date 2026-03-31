"""Session and message persistence with PostgreSQL + in-memory fallback."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from sqlalchemy import select

from app.core.db import (
    ChatMessageRecord,
    ChatSessionRecord,
    db_session,
    is_database_online,
)
from app.core.llm import get_llm
from app.core.tools import get_current_datetime, get_tools
from app.domain.partners import PARTNERS, get_system_prompt

logger = logging.getLogger("session_manager")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

MAX_TOOL_ROUNDS = 5

# In-memory fallback for local runs where DATABASE_URL is not configured
_local: dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_iso(value: datetime | str | None) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return value or _now_iso()


def _serialize_session(record: ChatSessionRecord) -> dict:
    return {
        "session_id": record.session_id,
        "user_id": record.user_id,
        "partner_id": record.partner_id,
        "partner_name": record.partner_name,
        "user_name": record.user_name,
        "nickname": record.nickname,
        "user_age": record.user_age,
        "language": record.language,
        "interests": list(record.interests or []),
        "personality_pref": record.personality_pref,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "created_at": _to_iso(record.created_at),
        "last_active": _to_iso(record.last_active),
        "message_count": record.message_count,
    }


class SessionData:
    def __init__(self, data: dict):
        self._d = data

    @property
    def session_id(self) -> str: return self._d["session_id"]
    @property
    def user_id(self) -> str: return self._d["user_id"]
    @property
    def partner_id(self) -> str: return self._d["partner_id"]
    @property
    def partner_name(self) -> str: return self._d["partner_name"]
    @property
    def user_name(self) -> str: return self._d["user_name"]
    @property
    def nickname(self) -> str: return self._d.get("nickname", self._d["user_name"])
    @property
    def user_age(self) -> int: return self._d["user_age"]
    @property
    def language(self) -> str: return self._d["language"]
    @property
    def interests(self) -> list: return self._d.get("interests", [])
    @property
    def personality_pref(self) -> Optional[str]: return self._d.get("personality_pref")
    @property
    def created_at(self) -> str: return self._d["created_at"]
    @property
    def last_active(self) -> str: return self._d["last_active"]
    @property
    def message_count(self) -> int: return self._d["message_count"]
    @property
    def latitude(self) -> Optional[float]: return self._d.get("latitude")
    @property
    def longitude(self) -> Optional[float]: return self._d.get("longitude")

    def to_info(self) -> dict:
        return {k: v for k, v in self._d.items() if k != "history"}


def _get_local_session(session_id: str, user_id: Optional[str] = None) -> dict | None:
    data = _local.get(session_id)
    if not data:
        return None
    if user_id and data.get("user_id") != user_id:
        return None
    return data


def create_session(
    *,
    user_id: str,
    partner_id: str,
    user_name: str,
    nickname: Optional[str] = None,
    user_age: int = 22,
    language: str = "English",
    interests: Optional[list[str]] = None,
    personality_pref: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    api_key: Optional[str] = None,  # kept for backward compat; ignored
) -> SessionData:
    if partner_id not in PARTNERS:
        raise ValueError(f"Partner '{partner_id}' does not exist.")

    now = _now_iso()
    data: dict = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "partner_id": partner_id,
        "partner_name": PARTNERS[partner_id]["name"],
        "user_name": user_name,
        "nickname": nickname or user_name,
        "user_age": user_age,
        "language": language,
        "interests": interests or [],
        "personality_pref": personality_pref,
        "latitude": latitude,
        "longitude": longitude,
        "created_at": now,
        "last_active": now,
        "message_count": 0,
        "history": [],
    }

    if is_database_online():
        with db_session() as db:
            record = ChatSessionRecord(
                session_id=data["session_id"],
                user_id=user_id,
                partner_id=partner_id,
                partner_name=data["partner_name"],
                user_name=user_name,
                nickname=data["nickname"],
                user_age=user_age,
                language=language,
                interests=data["interests"],
                personality_pref=personality_pref,
                latitude=latitude,
                longitude=longitude,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return SessionData(_serialize_session(record))

    _local[data["session_id"]] = data
    return SessionData(data)


def get_session(session_id: str, user_id: Optional[str] = None) -> Optional[SessionData]:
    if is_database_online():
        with db_session() as db:
            stmt = select(ChatSessionRecord).where(ChatSessionRecord.session_id == session_id)
            if user_id:
                stmt = stmt.where(ChatSessionRecord.user_id == user_id)
            record = db.execute(stmt).scalar_one_or_none()
            return SessionData(_serialize_session(record)) if record else None

    data = _get_local_session(session_id, user_id)
    return SessionData(data) if data else None


def _get_history_records(db, session_id: str) -> list[ChatMessageRecord]:
    stmt = (
        select(ChatMessageRecord)
        .where(ChatMessageRecord.session_id == session_id)
        .order_by(ChatMessageRecord.created_at.asc(), ChatMessageRecord.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def send_message(session_id: str, message: str, user_id: str) -> str:
    if is_database_online():
        with db_session() as db:
            session_record = db.execute(
                select(ChatSessionRecord).where(
                    ChatSessionRecord.session_id == session_id,
                    ChatSessionRecord.user_id == user_id,
                )
            ).scalar_one_or_none()
            if not session_record:
                raise KeyError(f"Session '{session_id}' not found.")

            data = _serialize_session(session_record)
            history = _get_history_records(db, session_id)
            history_turns = [{"role": h.role, "text": h.text} for h in history]
            reply = _generate_reply(data, history_turns, message)

            now = datetime.now(timezone.utc)
            db.add(ChatMessageRecord(session_id=session_id, role="user", text=message, created_at=now))
            db.add(ChatMessageRecord(session_id=session_id, role="model", text=reply, created_at=now))
            session_record.message_count = int(session_record.message_count) + 1
            session_record.last_active = now
            db.commit()
            return reply

    data = _get_local_session(session_id, user_id)
    if not data:
        raise KeyError(f"Session '{session_id}' not found.")
    reply = _generate_reply(data, data.get("history", []), message)
    data["history"].append({"role": "user", "text": message})
    data["history"].append({"role": "model", "text": reply})
    data["message_count"] += 1
    data["last_active"] = _now_iso()
    return reply


def _generate_reply(data: dict, history: list[dict], message: str) -> str:
    system_prompt = get_system_prompt(
        partner_id=data["partner_id"],
        user_name=data["user_name"],
        nickname=data.get("nickname", data["user_name"]),
        user_age=data["user_age"],
        language=data["language"],
        interests=data.get("interests", []),
        personality_pref=data.get("personality_pref"),
    )

    dt = get_current_datetime()
    ctx_lines = [
        "\n[CONTEXT - injected, never mention these meta-details to the user]",
        f"Current date/time: {dt['date']}, {dt['time_utc']}",
    ]
    system_prompt += "\n" + "\n".join(ctx_lines)

    messages: list = [SystemMessage(content=system_prompt)]
    for msg in history:
        text = msg.get("text", "")
        if not text:
            continue
        if msg["role"] == "user":
            messages.append(HumanMessage(content=text))
        else:
            messages.append(AIMessage(content=text))
    messages.append(HumanMessage(content=message))

    tools = get_tools(
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
    )
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    tool_map: dict = {}
    for tool in tools:
        name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if name:
            tool_map[name] = tool
            tool_map[name.lower()] = tool
        lname = str(name or "").lower()
        if "search" in lname or "web" in lname:
            tool_map.setdefault("search", tool)
            tool_map.setdefault("web_search", tool)

    response = None
    for round_idx in range(MAX_TOOL_ROUNDS + 1):
        logger.info("LLM invoke round %d - messages=%d", round_idx + 1, len(messages))
        response = llm_with_tools.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []
        logger.info("LLM returned - tool_calls_count=%d", len(tool_calls))
        if not tool_calls:
            break

        messages.append(response)
        logger.info("Appended model response to messages (contains tool calls).")

        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_id = tc.get("id")
            tool_args = tc.get("args") or {}
            logger.info("Executing tool '%s' (id=%s) with args=%s", tool_name, tool_id, tool_args)

            tool_fn = tool_map.get(tool_name)
            if tool_fn is None:
                result = {"error": f"Unknown tool: {tool_name}"}
                logger.error("Unknown tool requested: %s", tool_name)
            else:
                try:
                    try:
                        raw = tool_fn.invoke(tool_args)
                    except TypeError:
                        if isinstance(tool_args, dict):
                            if "query" in tool_args:
                                query_arg = tool_args.get("query")
                            elif "queries" in tool_args and isinstance(tool_args.get("queries"), (list, tuple)):
                                queries = tool_args.get("queries")
                                query_arg = queries[0] if queries else ""
                            elif len(tool_args) == 1:
                                query_arg = next(iter(tool_args.values()))
                            else:
                                query_arg = str(tool_args)
                        else:
                            query_arg = tool_args
                        raw = tool_fn.invoke(query_arg)

                    result = raw if isinstance(raw, dict) else {"result": raw}
                except Exception as exc:
                    result = {"error": str(exc)}
                    logger.exception("Exception while running tool '%s': %s", tool_name, exc)

            messages.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_id,
                )
            )

    if response is None:
        raise RuntimeError("Model returned no response.")

    reply_text = response.content
    if isinstance(reply_text, list):
        parts = []
        for block in reply_text:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        reply_text = " ".join(parts).strip()

    if not reply_text:
        raise RuntimeError("Model returned an empty reply.")
    return reply_text


def get_history(session_id: str, user_id: str) -> list[dict]:
    if is_database_online():
        with db_session() as db:
            session_record = db.execute(
                select(ChatSessionRecord).where(
                    ChatSessionRecord.session_id == session_id,
                    ChatSessionRecord.user_id == user_id,
                )
            ).scalar_one_or_none()
            if not session_record:
                raise KeyError(f"Session '{session_id}' not found.")
            messages = _get_history_records(db, session_id)
            return [{"role": m.role, "text": m.text} for m in messages]

    data = _get_local_session(session_id, user_id)
    if data is None:
        raise KeyError(f"Session '{session_id}' not found.")
    return data.get("history", [])


def delete_session(session_id: str, user_id: str) -> bool:
    if is_database_online():
        with db_session() as db:
            record = db.execute(
                select(ChatSessionRecord).where(
                    ChatSessionRecord.session_id == session_id,
                    ChatSessionRecord.user_id == user_id,
                )
            ).scalar_one_or_none()
            if not record:
                return False
            db.delete(record)
            db.commit()
            return True

    data = _get_local_session(session_id, user_id)
    if not data:
        return False
    del _local[session_id]
    return True


def list_sessions(user_id: str) -> list[dict]:
    if is_database_online():
        with db_session() as db:
            stmt = (
                select(ChatSessionRecord)
                .where(ChatSessionRecord.user_id == user_id)
                .order_by(ChatSessionRecord.last_active.desc())
            )
            records = db.execute(stmt).scalars().all()
            return [_serialize_session(record) for record in records]

    items = [SessionData(data).to_info() for data in _local.values() if data.get("user_id") == user_id]
    return sorted(
        items,
        key=lambda item: item.get("last_active") or item.get("created_at") or "",
        reverse=True,
    )
