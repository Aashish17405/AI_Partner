"""
LLM Factory — returns a LangChain BaseChatModel based on the LLM_PROVIDER env var.

Supported providers
-------------------
  openai  (default) — OpenAI GPT  via langchain-openai
  groq              — Groq Cloud  via langchain-groq

Configuration
-------------
Set LLM_PROVIDER to the desired provider, then set the corresponding API key:

  Provider  | Env var          | Default model
  ----------|------------------|----------------------------
  openai    | OPENAI_API_KEY   | gpt-4o
  groq      | GROQ_API_KEY     | mixtral-8x7b-32768

Optionally override the model name via:
  OPENAI_MODEL / GROQ_MODEL

Switching providers requires only a change in env vars — no code changes.
"""

from __future__ import annotations

import os

from langchain_core.language_models import BaseChatModel


def get_llm() -> BaseChatModel:
    """
    Instantiate and return the configured chat model.

    Raises
    ------
    ValueError   — if LLM_PROVIDER is not recognised.
    ImportError  — if the required langchain provider package is missing.
    EnvironmentError — if the required API key env var is not set.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to your .env or environment variables."
            )
        try:
            from langchain_openai import ChatOpenAI  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for the 'openai' provider. "
                "Run: pip install langchain-openai"
            ) from exc

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=api_key,
            temperature=1.0,
        )

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. Add it to your .env or environment variables."
            )
        try:
            from langchain_groq import ChatGroq  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "langchain-groq is required for the 'groq' provider. "
                "Run: pip install langchain-groq"
            ) from exc

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
            api_key=api_key,
            temperature=1.0,
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            "Valid values: openai, groq"
        )
