"""FastAPI app entrypoint.

`uvicorn doc_chat_api.main:app` boots the production server. Tests use
`build_app(connect_db=False)` to get an app instance without touching Postgres.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doc_chat_api.agents.doc_chat_agent import build_agent
from doc_chat_api.db import Database
from doc_chat_api.routes import chat as chat_routes
from doc_chat_api.routes import documents as documents_routes
from doc_chat_api.s3 import S3Client
from doc_chat_api.settings import Settings


def build_app(connect_db: bool = True) -> FastAPI:
    """Build the FastAPI app. Tests pass connect_db=False to skip the lifespan
    Postgres connect (which would otherwise fail without a real DB)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if connect_db:
            settings = Settings()
            app.state.db = Database(settings.database_url)
            await app.state.db.connect()
            app.state.s3 = S3Client(bucket=settings.documents_bucket, region=settings.aws_region)
            app.state.agent = build_agent(settings.bedrock_model_id)
        yield
        if connect_db and getattr(app.state, "db", None) is not None:
            await app.state.db.disconnect()

    app = FastAPI(title="doc-chat-api", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # demo runs on a single Coder workspace; everything is same-host
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(documents_routes.router)
    app.include_router(chat_routes.router)
    return app


app = build_app()
