"""Environment-backed application configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_clean_env(key: str, default: str = "") -> str:
    """Read env and strip quotes, spaces, and carriage returns."""
    val = os.getenv(key, default) or default
    return val.strip().strip("'\"").replace("\r", "").replace("\n", "")


LLM_PROVIDER = _get_clean_env("LLM_PROVIDER", "openai").lower()
LLM_PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}

REQUIRED_LLM_KEY = LLM_PROVIDER_KEY_MAP.get(LLM_PROVIDER, "OPENAI_API_KEY")

SUPABASE_URL = _get_clean_env("SUPABASE_URL", "https://cxzcjsnlisxrvwcviksg.supabase.co").rstrip("/")
SUPABASE_JWT_AUDIENCE = _get_clean_env("SUPABASE_JWT_AUDIENCE", "authenticated")
SUPABASE_ANON_KEY = _get_clean_env("SUPABASE_ANON_KEY")
SUPABASE_JWT_SECRET = _get_clean_env("SUPABASE_JWT_SECRET")

DATABASE_URL = (
    _get_clean_env("DATABASE_URL")
    or _get_clean_env("SUPABASE_DB_URL")
)

ALLOWED_ORIGINS = [
    "https://ai-partner-ui.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://ai-partner.dev-aashish.tech",
]


def validate_runtime_config() -> None:
    """Fail fast when mandatory provider credentials are missing."""
    if not os.getenv(REQUIRED_LLM_KEY, ""):
        raise EnvironmentError(
            f"{REQUIRED_LLM_KEY} is not set for LLM_PROVIDER='{LLM_PROVIDER}'. "
            "Add it to your .env file or environment variables."
        )
    if not SUPABASE_ANON_KEY:
        raise EnvironmentError(
            "SUPABASE_ANON_KEY is not set. Add your Supabase anon key to backend .env."
        )
