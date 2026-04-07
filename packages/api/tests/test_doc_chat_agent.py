# packages/api/tests/test_doc_chat_agent.py
"""Unit tests for doc_chat_agent — verify history conversion only.

The actual Bedrock call is integration-tested in test_chat.py and skipped
without BEDROCK_MODEL_ID. Here we just check the helpers.
"""
from doc_chat_api.agents.doc_chat_agent import db_history_to_pydantic_ai_messages


def test_db_history_to_pydantic_ai_messages_empty() -> None:
    assert db_history_to_pydantic_ai_messages([]) == []


def test_db_history_to_pydantic_ai_messages_alternates_roles() -> None:
    rows = [
        {"role": "user", "content": "what is this about?"},
        {"role": "assistant", "content": "It's a paper on cats."},
        {"role": "user", "content": "tell me more"},
    ]
    messages = db_history_to_pydantic_ai_messages(rows)
    assert len(messages) == 3
    # The function returns ModelMessage instances; each carries the original
    # text content. We assert on a serialized form to keep the test stable
    # across pydantic-ai versions.
    serialized = [str(m) for m in messages]
    assert "what is this about" in serialized[0]
    assert "It's a paper on cats" in serialized[1]
    assert "tell me more" in serialized[2]
