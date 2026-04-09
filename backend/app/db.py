import os
from typing import Any

import asyncpg
from fastapi import HTTPException

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    """Initialize the asyncpg connection pool. Call on app startup."""
    global _pool
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    _pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)


async def close_pool() -> None:
    """Close the connection pool. Call on app shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def execute_read_query(sql: str) -> dict[str, Any]:
    """
    Execute a read-only SQL query and return columns + rows.
    Raises HTTP 503 if the database is unreachable.
    """
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        async with _pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                records = await conn.fetch(sql)

        if not records:
            return {"columns": [], "rows": []}

        columns = list(records[0].keys())
        rows = [list(r.values()) for r in records]
        return {"columns": columns, "rows": rows}

    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
