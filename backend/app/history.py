import json
import os
from datetime import datetime, date
from decimal import Decimal

import aiosqlite

from app.schemas import HistoryRecord

DB_PATH = os.getenv("HISTORY_DB_PATH", "/tmp/supachat_history.db")


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS query_history (
    query_id   TEXT PRIMARY KEY,
    session_id TEXT NOT NULL DEFAULT '',
    nl_query   TEXT NOT NULL,
    sql        TEXT NOT NULL DEFAULT '',
    summary    TEXT NOT NULL DEFAULT '',
    columns    TEXT NOT NULL DEFAULT '[]',
    rows       TEXT NOT NULL DEFAULT '[]',
    chart_type TEXT NOT NULL DEFAULT 'none',
    chart_data TEXT NOT NULL DEFAULT '[]',
    timestamp  TEXT NOT NULL,
    error      TEXT
)
"""


async def init_history_db() -> None:
    """Create the history table if it doesn't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def save_query(record: HistoryRecord) -> None:
    """Persist a HistoryRecord to SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO query_history
                (query_id, session_id, nl_query, sql, summary,
                 columns, rows, chart_type, chart_data, timestamp, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.query_id,
                record.session_id,
                record.nl_query,
                record.sql,
                record.summary,
                json.dumps(record.columns, default=_json_default),
                json.dumps(record.rows, default=_json_default),
                record.chart_type,
                json.dumps(record.chart_data, default=_json_default),
                record.timestamp.isoformat(),
                record.error,
            ),
        )
        await db.commit()


async def get_history(limit: int = 50) -> list[HistoryRecord]:
    """Return the most recent `limit` history records, newest first."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM query_history
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()

    return [
        HistoryRecord(
            query_id=row["query_id"],
            session_id=row["session_id"],
            nl_query=row["nl_query"],
            sql=row["sql"],
            summary=row["summary"],
            columns=json.loads(row["columns"]),
            rows=json.loads(row["rows"]),
            chart_type=row["chart_type"],
            chart_data=json.loads(row["chart_data"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            error=row["error"],
        )
        for row in rows
    ]


async def delete_history_record(query_id: str) -> bool:
    """Delete a single history record. Returns True if a row was deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM query_history WHERE query_id = ?", (query_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_history() -> int:
    """Delete all history records. Returns the number of rows deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM query_history")
        await db.commit()
        return cursor.rowcount
