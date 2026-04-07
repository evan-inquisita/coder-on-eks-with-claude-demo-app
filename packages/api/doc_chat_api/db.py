"""Async Postgres pool wrapper.

The pool is created on FastAPI startup (see main.py lifespan) and closed on shutdown.
Routes acquire connections via `db.acquire()`.
"""

from __future__ import annotations

from typing import Any

import asyncpg


class Database:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )

    async def disconnect(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    def acquire(self) -> Any:
        """Return a connection acquisition context manager.

        Usage:
            async with db.acquire() as conn:
                row = await conn.fetchrow("SELECT 1")
        """
        if self.pool is None:
            raise RuntimeError("Database.acquire() called before connect()")
        return self.pool.acquire()
