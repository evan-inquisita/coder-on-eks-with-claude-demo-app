"""Chat routes — message history and posting new messages.

The agent and chat function are pulled from app.state so tests can swap them
for a fake without monkeypatching pydantic-ai or Bedrock.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from doc_chat_api.agents.doc_chat_agent import chat_with_document

router = APIRouter(tags=["chat"])


class PostMessageBody(BaseModel):
    content: str


@router.get("/documents/{doc_id}/messages")
async def get_messages(request: Request, doc_id: UUID) -> list[dict]:
    db = request.app.state.db
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content, created_at FROM messages
            WHERE document_id = $1
            ORDER BY created_at ASC
            """,
            doc_id,
        )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


@router.post("/documents/{doc_id}/messages")
async def post_message(request: Request, doc_id: UUID, body: PostMessageBody) -> dict:
    db = request.app.state.db
    s3 = request.app.state.s3
    agent = request.app.state.agent
    chat_fn = getattr(request.app.state, "chat_fn", chat_with_document)

    async with db.acquire() as conn:
        doc = await conn.fetchrow("SELECT id, s3_key FROM documents WHERE id = $1", doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="document not found")

        history_rows = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE document_id = $1 ORDER BY created_at ASC
            """,
            doc_id,
        )

        # Persist the user message before calling the agent so it shows up in
        # history if the agent call fails halfway through.
        await conn.execute(
            "INSERT INTO messages (document_id, role, content) VALUES ($1, $2, $3)",
            doc_id,
            "user",
            body.content,
        )

        pdf_bytes = await s3.get_object(key=doc["s3_key"])
        assistant_text = await chat_fn(agent, pdf_bytes, list(history_rows), body.content)

        await conn.execute(
            "INSERT INTO messages (document_id, role, content) VALUES ($1, $2, $3)",
            doc_id,
            "assistant",
            assistant_text,
        )

    return {"role": "assistant", "content": assistant_text}
