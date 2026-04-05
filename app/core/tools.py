"""
Agent tools — LangChain @tool decorated functions, callable by any provider.

Available tools
---------------
datetime_tool          — Returns current UTC date & time.
location_tool          — Reverse-geocodes stored lat/lon into city/country.
web_search             — Optional web/news search (Tavily if key is set,
                         DuckDuckGo otherwise). Can be disabled via
                         ENABLE_WEB_SEARCH=false.

All tools are provider-agnostic and work with OpenAI and Groq
through LangChain's unified tool-calling interface.

Session tools are built via get_tools(latitude, longitude) which
pre-binds location coordinates so the LLM can call them without arguments.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Optional
import logging

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Pure implementations (usable directly without going through the LLM)
# ---------------------------------------------------------------------------

def get_current_datetime() -> dict:
    """Return the current UTC date and time as a structured dict."""
    now = datetime.now(timezone.utc)
    return {
        "date": now.strftime("%A, %B %d, %Y"),      # e.g. "Saturday, March 01, 2026"
        "time_utc": now.strftime("%H:%M:%S UTC"),    # e.g. "14:35:22 UTC"
        "iso8601": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.year,
    }


def get_user_location(latitude: Optional[float], longitude: Optional[float]) -> dict:
    """
    Reverse-geocode a lat/lon pair using OpenStreetMap Nominatim (free, no key).
    Returns city, state, country, and a human-readable display string.
    Falls back gracefully if the API is unreachable.
    """
    if latitude is None or longitude is None:
        return {"error": "Location coordinates are not available for this session."}

    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?lat={latitude}&lon={longitude}&format=json&zoom=10"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AICompanionSAAS/1.0 (contact@aicompanion.app)"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        addr = data.get("address", {})
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("county")
            or "Unknown city"
        )
        state = addr.get("state", "")
        country = addr.get("country", "Unknown country")
        country_code = addr.get("country_code", "").upper()

        display = city
        if state and state != city:
            display += f", {state}"
        display += f", {country}"

        return {
            "city": city,
            "state": state,
            "country": country,
            "country_code": country_code,
            "display": display,
            "latitude": latitude,
            "longitude": longitude,
        }

    except Exception as exc:  # network error, timeout, parse error
        return {
            "error": f"Could not retrieve location: {exc}",
            "latitude": latitude,
            "longitude": longitude,
        }


# ---------------------------------------------------------------------------
# Static LangChain tools (no session-specific state needed)
# ---------------------------------------------------------------------------

@tool
def datetime_tool() -> dict:
    """
    Returns the current date and time in UTC.
    Use this whenever the user asks what time or date it is, or when a
    time-aware response is helpful (good morning / night greetings,
    event countdowns, wishing happy new year, etc.).
    """
    return get_current_datetime()


# ---------------------------------------------------------------------------
# Dynamic location tool — factory captures session coordinates via closure
# ---------------------------------------------------------------------------

def _make_location_tool(latitude: Optional[float], longitude: Optional[float]):
    """
    Return a LangChain @tool bound to this session's GPS coordinates.
    The LLM calls it with no arguments; coordinates are captured in the closure.
    """

    @tool
    def location_tool() -> dict:
        """
        Returns the user's current city and country based on their GPS coordinates.
        Use this when the user asks where they are, mentions wanting local
        recommendations, asks about nearby places, or when location context
        would personalise the response.
        """
        return get_user_location(latitude, longitude)

    return location_tool


# ---------------------------------------------------------------------------
# Optional web search tool
# ---------------------------------------------------------------------------

ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").strip().lower() in {
    "1", "true", "yes", "on",
}


def _make_search_tool():
    """
    Return a web search tool if enabled and a backend is available.

    Priority:
      1. Tavily  (requires TAVILY_API_KEY)  — highest quality
      2. DuckDuckGo (no API key required)   — free fallback
      3. None   — search disabled or packages missing

    The returned tool is always wrapped in a custom @tool with an explicit
    description so LLMs know exactly when to call it.
    """
    if not ENABLE_WEB_SEARCH:
        return None

    _backend = None

    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key:
        try:
            from langchain_tavily import TavilySearchResults  # type: ignore[import]
            _backend = TavilySearchResults(max_results=4, api_key=tavily_key)
        except ImportError:
            pass

    if _backend is None:
        try:
            from langchain_community.tools import DuckDuckGoSearchRun  # type: ignore[import]
            _backend = DuckDuckGoSearchRun()
        except ImportError:
            pass

    if _backend is None:
        return None

    # Wrap with an explicit, LLM-facing description so the model knows it MUST
    # call this tool before answering any question about current events.
    _search_fn = _backend

    @tool
    def web_search(*args, **kwargs) -> str:
        """
        Search the internet for up-to-date information.

        You MUST call this tool BEFORE forming any response about:
        - sports match results, scores, highlights, or player stats
          (cricket, football, IPL, World Cup, Champions Trophy, etc.)
        - recent news, breaking headlines, or trending topics
        - current movies, box office, OTT releases, or reviews
        - any real-world event that happened in the last few months
        - weather, stock prices, or anything that changes over time

        Do NOT guess or rely on memory for these — always search first.
        If the user mentions India's match, a recent series, or any live
        event, call this tool with a specific search query before replying.
        """
        logger = logging.getLogger("tools.web_search")

        # Support different invocation shapes from various LLM providers:
        # - single positional string: web_search("query")
        # - kwargs: web_search(query="...")
        # - kwargs: web_search(queries=["q1","q2"]) (Tavily style)
        query = None
        if args:
            # take first positional arg
            query = args[0]
        elif "query" in kwargs:
            query = kwargs.get("query")
        elif "queries" in kwargs and isinstance(kwargs.get("queries"), (list, tuple)):
            qs = kwargs.get("queries")
            query = qs[0] if qs else ""
        else:
            # fallback: stringify whatever was passed
            query = str(kwargs)

        logger.info("web_search called with query: %s", str(query)[:200])
        result = _search_fn.invoke(query)
        try:
            if isinstance(result, list):
                # Tavily returns a list of dicts with 'content' keys
                joined = "\n\n".join(r.get("content", str(r)) for r in result)
                logger.info("web_search returned %d results", len(result))
                return joined
            logger.info("web_search returned: %s", str(result)[:200])
            return str(result)
        except Exception as exc:
            logger.exception("Error processing web_search results: %s", exc)
            return str(result)

    return web_search


# ---------------------------------------------------------------------------
# Long-term memory tool — factory captures user_id for persistence
# ---------------------------------------------------------------------------

def _make_memory_tool(user_id: str):
    """
    Return a LangChain @tool bound to this specific user's database records.
    The AI calls this to store facts that should be remembered across sessions.
    """
    from app.core.db import db_session, UserMemoryRecord

    @tool
    def save_memory(content: str, memory_type: str = "fact", importance: int = 3) -> str:
        """
        Saves a compact, meaningful fact or preference about the user to long-term memory.
        Use this whenever the user shares something they'd expect you to remember in 
        future sessions (e.g., location, workplace, specific life plans, birthdays, 
        pet peeves, favorite shows, relationship status).
        
        IMPORTANCE SCALE:
        1: Minor detail (current mood, what they ate for lunch)
        3: Standard fact (city they live in, their job, a hobby)
        5: Core identity (their birthday, their child's name, a major life trauma or win)
        
        Keep memories COMPACT (e.g., "User lives in Hyderabad", "User is free after 7pm tonight").
        """
        try:
            with db_session() as db:
                record = UserMemoryRecord(
                    user_id=user_id,
                    content=content.strip(),
                    memory_type=memory_type,
                    importance=importance
                )
                db.add(record)
                db.commit()
            return f"Memory successfully saved: '{content}'"
        except Exception as e:
            # Fallback for if DB is offline or other error
            return f"Note: could not save memory to persistent store ({e}). Memory only available in this session."

    return save_memory


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_tools(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    user_id: Optional[str] = None,
) -> list:
    """
    Build and return the complete agent tool list for a chat session.

    Always included:
      - datetime_tool
      - location_tool (pre-bound to session coordinates)
      - memory_tool (pre-bound to user_id for persistence)
    """
    tools = [
        datetime_tool,
        _make_location_tool(latitude, longitude),
    ]
    
    if user_id:
        tools.append(_make_memory_tool(user_id))
        
    search = _make_search_tool()
    if search:
        tools.append(search)
    return tools



