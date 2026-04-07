# packages/api/tests/test_chat_integration.py
"""End-to-end happy path: upload → list → post message → assert non-empty.

Skipped automatically unless BEDROCK_MODEL_ID is set AND a real Postgres is
reachable via DATABASE_URL. CI without AWS creds skips this test entirely.

To run locally inside a workspace after `make up`:
    DATABASE_URL=postgresql://doc_chat:doc_chat@localhost:5432/doc_chat \\
    DOCUMENTS_BUCKET=doc-chat-documents-<account-id> \\
    BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6-20250929-v1:0 \\
    uv run pytest tests/test_chat_integration.py -v -s
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from doc_chat_api.main import build_app


pytestmark = pytest.mark.skipif(
    not (
        os.getenv("BEDROCK_MODEL_ID")
        and os.getenv("DATABASE_URL")
        and os.getenv("DOCUMENTS_BUCKET")
    ),
    reason="Integration test requires BEDROCK_MODEL_ID, DATABASE_URL, DOCUMENTS_BUCKET",
)


@pytest.mark.asyncio
async def test_happy_path_upload_list_chat() -> None:
    app = build_app(connect_db=True)

    # Use AsyncClient with ASGITransport so the app's lifespan runs and we
    # exercise the real Postgres + S3 + Bedrock chain.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Trigger lifespan startup
        async with app.router.lifespan_context(app):
            pdf_bytes = Path(__file__).parent.joinpath("fixtures", "tiny.pdf").read_bytes()
            files = {"file": ("tiny.pdf", pdf_bytes, "application/pdf")}
            upload = await client.post("/documents", files=files)
            assert upload.status_code == 200, upload.text
            doc_id = upload.json()["id"]

            listing = await client.get("/documents")
            assert listing.status_code == 200
            assert any(d["id"] == doc_id for d in listing.json())

            chat = await client.post(
                f"/documents/{doc_id}/messages",
                json={"content": "Summarize this document in one sentence."},
            )
            assert chat.status_code == 200, chat.text
            assistant = chat.json()
            assert assistant["role"] == "assistant"
            assert len(assistant["content"]) > 0

            history = await client.get(f"/documents/{doc_id}/messages")
            assert history.status_code == 200
            messages = history.json()
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"

            # Cleanup
            await client.delete(f"/documents/{doc_id}")
