# packages/api/tests/test_db.py
import pytest
from doc_chat_api.db import Database


def test_database_constructor_stores_url() -> None:
    db = Database("postgresql://u:p@h:5432/d")
    assert db.dsn == "postgresql://u:p@h:5432/d"
    assert db.pool is None  # not connected yet


@pytest.mark.asyncio
async def test_database_connect_disconnect_lifecycle_calls_asyncpg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Database.connect calls asyncpg.create_pool with the right DSN.

    We monkeypatch asyncpg.create_pool to avoid needing a real Postgres for this unit test.
    """
    import doc_chat_api.db as db_module

    captured: dict = {}

    class FakePool:
        async def close(self) -> None:
            captured["closed"] = True

    async def fake_create_pool(dsn: str, **kwargs: object) -> FakePool:
        captured["dsn"] = dsn
        captured["kwargs"] = kwargs
        return FakePool()

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)

    db = Database("postgresql://u:p@h:5432/d")
    await db.connect()
    assert captured["dsn"] == "postgresql://u:p@h:5432/d"
    assert db.pool is not None

    await db.disconnect()
    assert captured["closed"] is True
    assert db.pool is None
