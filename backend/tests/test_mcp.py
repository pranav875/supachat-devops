"""
Unit tests for MCP server tools (task 4.2).

Tests cover:
  - execute_query: successful execution, empty results, DB error handling
  - get_schema: returns expected table metadata
  - get_topics: successful fetch, empty topics, DB error handling
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_result(columns: list, rows: list) -> dict:
    return {"columns": columns, "rows": rows}


# ---------------------------------------------------------------------------
# execute_query tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_query_success():
    """execute_query returns columns and rows on a successful DB call."""
    mock_result = _make_db_result(
        ["article_id", "view_count"],
        [[1, 500], [2, 300]],
    )
    with patch("app.mcp_server.execute_read_query", new=AsyncMock(return_value=mock_result)):
        from app.mcp_server import execute_query
        result = await execute_query("SELECT article_id, view_count FROM article_views")

    assert result["columns"] == ["article_id", "view_count"]
    assert result["rows"] == [[1, 500], [2, 300]]


@pytest.mark.asyncio
async def test_execute_query_empty_results():
    """execute_query returns empty columns and rows when query yields no data."""
    mock_result = _make_db_result([], [])
    with patch("app.mcp_server.execute_read_query", new=AsyncMock(return_value=mock_result)):
        from app.mcp_server import execute_query
        result = await execute_query("SELECT * FROM articles WHERE id = -1")

    assert result["columns"] == []
    assert result["rows"] == []


@pytest.mark.asyncio
async def test_execute_query_db_error_raises_exception():
    """execute_query wraps DB errors in a descriptive Exception (req 2.3, 2.4)."""
    with patch(
        "app.mcp_server.execute_read_query",
        new=AsyncMock(side_effect=HTTPException(status_code=503, detail="Database unavailable")),
    ):
        from app.mcp_server import execute_query
        with pytest.raises(Exception, match="Query failed"):
            await execute_query("SELECT 1")


@pytest.mark.asyncio
async def test_execute_query_generic_error_raises_exception():
    """execute_query wraps any unexpected error with a descriptive message."""
    with patch(
        "app.mcp_server.execute_read_query",
        new=AsyncMock(side_effect=RuntimeError("connection reset")),
    ):
        from app.mcp_server import execute_query
        with pytest.raises(Exception, match="Query failed: connection reset"):
            await execute_query("SELECT 1")


# ---------------------------------------------------------------------------
# get_schema tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_schema_returns_all_tables():
    """get_schema returns metadata for all three expected tables (req 2.1)."""
    from app.mcp_server import get_schema
    schema = await get_schema()

    assert "articles" in schema
    assert "article_views" in schema
    assert "article_engagement" in schema


@pytest.mark.asyncio
async def test_get_schema_articles_columns():
    """articles table schema contains expected columns."""
    from app.mcp_server import get_schema
    schema = await get_schema()

    cols = schema["articles"]["columns"]
    assert "id" in cols
    assert "title" in cols
    assert "topic" in cols
    assert "published_at" in cols


@pytest.mark.asyncio
async def test_get_schema_has_descriptions():
    """Each table entry includes a description field."""
    from app.mcp_server import get_schema
    schema = await get_schema()

    for table, meta in schema.items():
        assert "description" in meta, f"Missing description for table '{table}'"
        assert "columns" in meta, f"Missing columns for table '{table}'"


# ---------------------------------------------------------------------------
# get_topics tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_topics_success():
    """get_topics returns a dict with a 'topics' list (req 2.1, 2.2)."""
    mock_result = _make_db_result(["topic"], [["AI"], ["DevOps"], ["Python"]])
    with patch("app.mcp_server.execute_read_query", new=AsyncMock(return_value=mock_result)):
        from app.mcp_server import get_topics
        result = await get_topics()

    assert "topics" in result
    assert result["topics"] == ["AI", "DevOps", "Python"]


@pytest.mark.asyncio
async def test_get_topics_empty():
    """get_topics returns an empty list when no topics exist."""
    mock_result = _make_db_result([], [])
    with patch("app.mcp_server.execute_read_query", new=AsyncMock(return_value=mock_result)):
        from app.mcp_server import get_topics
        result = await get_topics()

    assert result["topics"] == []


@pytest.mark.asyncio
async def test_get_topics_db_error_propagates():
    """get_topics propagates DB errors so callers can handle them (req 2.4)."""
    with patch(
        "app.mcp_server.execute_read_query",
        new=AsyncMock(side_effect=HTTPException(status_code=503, detail="Database unavailable")),
    ):
        from app.mcp_server import get_topics
        with pytest.raises(HTTPException) as exc_info:
            await get_topics()

    assert exc_info.value.status_code == 503
