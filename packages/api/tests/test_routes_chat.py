# packages/api/tests/test_routes_chat.py
"""Route-shape tests for chat endpoints. Stubs out the agent so we don't
hit Bedrock here — that's covered by Task 10's integration test."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from doc_chat_api.routes import chat as chat_routes


DOC_ID = uuid4()


class FakeConn:
    def __init__(self, store: dict[str, Any]) -> None:
        self.store = store

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        if "FROM documents" in query:
            return self.store.get("doc")
        return None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        if "FROM messages" in query:
            return self.store.setdefault("messages", [])
        return []

    async def execute(self, query: str, *args: Any) -> str:
        if "INSERT INTO messages" in query:
            self.store.setdefault("messages", []).append({"role": args[1], "content": args[2]})
        return "INSERT 1"


class FakeAcquire:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    async def __aenter__(self) -> FakeConn:
        return self.conn

    async def __aexit__(self, *exc: Any) -> None:
        return None


class FakeDb:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {"doc": {"id": DOC_ID, "s3_key": "documents/x/test.pdf"}}
        self.conn = FakeConn(self.store)

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.conn)


class FakeS3:
    async def get_object(self, key: str) -> bytes:
        return b"%PDF-1.4 fake"


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    db = FakeDb()
    s3 = FakeS3()

    async def fake_chat(agent, pdf_bytes, history_rows, user_message):  # noqa: ANN001
        return f"echo: {user_message}"

    app.state.db = db
    app.state.s3 = s3
    app.state.agent = object()  # opaque, never called by the fake
    app.state.chat_fn = fake_chat

    app.include_router(chat_routes.router)
    return TestClient(app)


def test_get_messages_empty(client: TestClient) -> None:
    response = client.get(f"/documents/{DOC_ID}/messages")
    assert response.status_code == 200
    assert response.json() == []


def test_post_message_returns_assistant_response_and_persists_both(client: TestClient) -> None:
    response = client.post(
        f"/documents/{DOC_ID}/messages",
        json={"content": "what is this about?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert "echo: what is this about?" in body["content"]

    history = client.get(f"/documents/{DOC_ID}/messages").json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
