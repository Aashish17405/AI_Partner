"""FastAPI app assembly and middleware wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import ALLOWED_ORIGINS, validate_runtime_config
from app.core.db import init_database

validate_runtime_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    print("AI Companion API is up.")
    yield
    print("AI Companion API shutting down.")


app = FastAPI(
    title="AI Companion SAAS",
    description=(
        "Choose your AI companion — virtual girlfriend, boyfriend, or best friend — "
        "and have deeply personal, private conversations powered by AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
