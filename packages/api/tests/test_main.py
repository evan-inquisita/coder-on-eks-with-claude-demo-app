# packages/api/tests/test_main.py
"""Smoke test that the app builds and /healthz responds."""
from fastapi.testclient import TestClient

from doc_chat_api.main import build_app


def test_build_app_returns_fastapi_with_routes() -> None:
    app = build_app(connect_db=False)
    paths = {route.path for route in app.routes}
    assert "/healthz" in paths
    assert "/documents" in paths
    assert "/documents/{doc_id}" in paths
    assert "/documents/{doc_id}/messages" in paths


def test_healthz_returns_ok() -> None:
    app = build_app(connect_db=False)
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
