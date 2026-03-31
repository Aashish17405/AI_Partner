"""Environment-backed application configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
LLM_PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}

REQUIRED_LLM_KEY = LLM_PROVIDER_KEY_MAP.get(LLM_PROVIDER, "OPENAI_API_KEY")

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://cxzcjsnlisxrvwcviksg.supabase.co",
).strip().rstrip("/")
SUPABASE_JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()

DATABASE_URL = (
    os.getenv("DATABASE_URL", "").strip()
    or os.getenv("SUPABASE_DB_URL", "").strip()
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
