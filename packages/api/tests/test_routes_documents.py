# packages/api/tests/test_routes_documents.py
"""Route-shape tests using FastAPI's TestClient with stubbed db + s3.

We don't hit a real Postgres or S3 here — Task 10's test_chat.py is the
end-to-end happy-path test (skipped without BEDROCK_MODEL_ID).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from doc_chat_api.routes import documents as documents_routes


class FakeConn:
    def __init__(self, store: dict[str, Any]) -> None:
        self.store = store

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        if "INSERT INTO documents" in query:
            doc_id = uuid4()
            row = {
                "id": doc_id,
                "name": args[0],
                "s3_key": args[1],
                "size_bytes": args[2],
            }
            self.store["docs"][str(doc_id)] = row
            return row
        if "SELECT" in query and "WHERE id" in query:
            return self.store["docs"].get(str(args[0]))
        return None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        if "FROM documents" in query:
            return list(self.store["docs"].values())
        return []

    async def execute(self, query: str, *args: Any) -> str:
        if "DELETE FROM documents" in query:
            self.store["docs"].pop(str(args[0]), None)
        return "DELETE 1"


class FakeAcquire:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    async def __aenter__(self) -> FakeConn:
        return self.conn

    async def __aexit__(self, *exc: Any) -> None:
        return None


class FakeDb:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {"docs": {}}
        self.conn = FakeConn(self.store)

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.conn)


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    @staticmethod
    def key_for_document(doc_id: str, filename: str) -> str:
        return f"documents/{doc_id}/{filename}"

    async def put_object(self, key: str, body: bytes, content_type: str) -> None:
        self.objects[key] = body

    async def get_object(self, key: str) -> bytes:
        return self.objects[key]

    async def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    db = FakeDb()
    s3 = FakeS3()
    app.state.db = db
    app.state.s3 = s3
    app.include_router(documents_routes.router)
    return TestClient(app)


def test_upload_document_returns_id_and_name(client: TestClient) -> None:
    files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
    response = client.post("/documents", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "test.pdf"
    assert "id" in body
    UUID(body["id"])  # parses


def test_list_documents_returns_uploaded(client: TestClient) -> None:
    client.post("/documents", files={"file": ("a.pdf", b"x", "application/pdf")})
    client.post("/documents", files={"file": ("b.pdf", b"y", "application/pdf")})
    response = client.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2
    names = sorted(d["name"] for d in docs)
    assert names == ["a.pdf", "b.pdf"]
