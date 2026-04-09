"""
MCP Server for SupaChat — exposes Supabase query tools to the LLM layer.

Tools registered:
  - execute_query(sql)  : run a read-only SQL query, return rows as JSON
  - get_schema()        : return table/column metadata for LLM prompt context
  - get_topics()        : return distinct topic list from the articles table
"""

from mcp.server.fastmcp import FastMCP

from app.db import execute_read_query

mcp = FastMCP("supachat")

# ---------------------------------------------------------------------------
# Schema metadata (static — mirrors 001_schema.sql)
# ---------------------------------------------------------------------------

_SCHEMA_INFO = {
    "articles": {
        "description": "Blog articles with metadata",
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "title": "TEXT NOT NULL",
            "topic": "TEXT NOT NULL",
            "author": "TEXT",
            "published_at": "TIMESTAMPTZ NOT NULL",
        },
    },
    "article_views": {
        "description": "Daily view counts per article",
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "article_id": "INT REFERENCES articles(id)",
            "viewed_date": "DATE NOT NULL",
            "view_count": "INT NOT NULL DEFAULT 0",
        },
    },
    "article_engagement": {
        "description": "Daily engagement metrics (likes, comments, shares) per article",
        "columns": {
            "id": "SERIAL PRIMARY KEY",
            "article_id": "INT REFERENCES articles(id)",
            "event_date": "DATE NOT NULL",
            "likes": "INT DEFAULT 0",
            "comments": "INT DEFAULT 0",
            "shares": "INT DEFAULT 0",
        },
    },
}


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def execute_query(sql: str) -> dict:
    """
    Execute a read-only SQL query against the Supabase blog analytics database.

    Args:
        sql: A valid PostgreSQL SELECT statement.

    Returns:
        A dict with 'columns' (list of str) and 'rows' (list of lists).
        Returns {'columns': [], 'rows': []} when the query yields no results.

    Raises:
        Exception with a descriptive message on DB errors or unreachable DB.
    """
    try:
        result = await execute_read_query(sql)
        return result
    except Exception as exc:
        # Surface a structured error so the LLM layer can handle it gracefully
        raise Exception(f"Query failed: {exc}") from exc


@mcp.tool()
async def get_schema() -> dict:
    """
    Return the blog analytics database schema as structured metadata.

    Returns:
        A dict mapping table names to their description and column definitions.
        Useful for building LLM prompts that need schema context.
    """
    return _SCHEMA_INFO


@mcp.tool()
async def get_topics() -> dict:
    """
    Return the distinct list of article topics present in the database.

    Returns:
        A dict with a 'topics' key containing a list of topic strings.
    """
    result = await execute_read_query(
        "SELECT DISTINCT topic FROM articles ORDER BY topic"
    )
    topics = [row[0] for row in result.get("rows", [])]
    return {"topics": topics}
