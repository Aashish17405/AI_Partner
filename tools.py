"""
Agent tools — callable by the Gemini model during chat.

Available tools
---------------
get_current_datetime   — Returns the current UTC date & time (human-readable).
get_user_location      — Reverse-geocodes stored lat/lon into a city / country string.

Both are exposed as Gemini FunctionDeclarations so the model can invoke them
autonomously whenever it decides the context calls for it (e.g. "what time is it?",
"where am I?", "suggest something near me").

The Google Search grounding tool is also included so the model can look up
live information (news, facts) in the same breath.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone

from google.genai import types


# ---------------------------------------------------------------------------
# Tool implementations  (pure Python — no AI involved)
# ---------------------------------------------------------------------------

def get_current_datetime() -> dict:
    """Return the current UTC date and time as a structured dict."""
    now = datetime.now(timezone.utc)
    return {
        "date": now.strftime("%A, %B %d, %Y"),          # e.g. "Saturday, March 01, 2026"
        "time_utc": now.strftime("%H:%M:%S UTC"),        # e.g. "14:35:22 UTC"
        "iso8601": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.year,
    }


def get_user_location(latitude: float, longitude: float) -> dict:
    """
    Reverse-geocode a lat/lon pair into a human-readable location using the
    OpenStreetMap Nominatim API (free, no key required).

    Returns a dict with city, state, country, and a formatted display string.
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

    except Exception as exc:  # network error, timeout, parse error …
        return {
            "error": f"Could not retrieve location: {exc}",
            "latitude": latitude,
            "longitude": longitude,
        }


# ---------------------------------------------------------------------------
# Gemini FunctionDeclarations
# ---------------------------------------------------------------------------

_datetime_decl = types.FunctionDeclaration(
    name="get_current_datetime",
    description=(
        "Returns the current date and time in UTC. "
        "Use this whenever the user asks what time or date it is, "
        "or when a time-aware response would be helpful (e.g. good morning/night greetings, "
        "wishing happy new year, etc.)."
    ),
    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
)

_location_decl = types.FunctionDeclaration(
    name="get_user_location",
    description=(
        "Returns the user's current city and country based on their GPS coordinates. "
        "Use this when the user asks where they are, mentions wanting local recommendations, "
        "asks about nearby places, or when location context would personalise the response."
    ),
    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
)


# ---------------------------------------------------------------------------
# Public: tool list to pass to GenerateContentConfig
# ---------------------------------------------------------------------------

AGENT_TOOLS: list[types.Tool] = [
    types.Tool(google_search=types.GoogleSearch()),
    types.Tool(function_declarations=[_datetime_decl, _location_decl]),
]


# ---------------------------------------------------------------------------
# Public: dispatch a function call by name
# ---------------------------------------------------------------------------

def dispatch_tool_call(name: str, args: dict, *, latitude=None, longitude=None) -> dict:
    """
    Execute the named tool and return its result dict.
    ``latitude`` and ``longitude`` are passed in from the session's stored coords.
    """
    if name == "get_current_datetime":
        return get_current_datetime()
    elif name == "get_user_location":
        return get_user_location(latitude, longitude)
    else:
        return {"error": f"Unknown tool: {name}"}
