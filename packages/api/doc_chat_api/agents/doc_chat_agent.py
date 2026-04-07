"""pydantic-ai agent for chatting with a single PDF document.

The agent receives the PDF as BinaryContent on every turn — no chunking,
no embedding. Bedrock Claude natively accepts PDFs and the demo's documents
are small. If you want to scale this beyond demo size, replace the
BinaryContent block with a retrieval step against pgvector.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.bedrock import BedrockConverseModel


SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about a single PDF document. "
    "Answer concisely and cite the parts of the document you used. "
    "If the document does not contain the answer, say so explicitly."
)


def build_agent(model_id: str) -> Agent:
    """Build a pydantic-ai Agent bound to a Bedrock Claude model."""
    return Agent(
        model=BedrockConverseModel(model_id),
        system_prompt=SYSTEM_PROMPT,
    )


def db_history_to_pydantic_ai_messages(rows: list[dict[str, Any]]) -> list[ModelMessage]:
    """Convert DB message rows into pydantic-ai ModelMessage history.

    Each row has shape {"role": "user" | "assistant", "content": str}. The
    pydantic-ai message history is alternating ModelRequest / ModelResponse.
    """
    messages: list[ModelMessage] = []
    for row in rows:
        if row["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=row["content"])]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=row["content"])]))
    return messages


async def chat_with_document(
    agent: Agent,
    pdf_bytes: bytes,
    history_rows: list[dict[str, Any]],
    user_message: str,
) -> str:
    """Run one chat turn against the document. Returns the assistant text."""
    history = db_history_to_pydantic_ai_messages(history_rows)
    result = await agent.run(
        [
            BinaryContent(data=pdf_bytes, media_type="application/pdf"),
            user_message,
        ],
        message_history=history,
    )
    return str(result.output)
