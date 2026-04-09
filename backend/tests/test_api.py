"""
Integration tests for the FastAPI application (task 9).

Tests use httpx.AsyncClient against the real app with:
  - A real Postgres instance (via DATABASE_URL env var, defaulting to a local test DB)
  - Mocked LLM calls to avoid external API dependencies

Covers:
  - GET /health                          (req 4.3)
  - POST /api/query success              (req 4.1, 4.2)
  - POST /api/query with bad SQL         (req 4.5)
  - POST /api/query with DB down         (req 4.5)
  - GET /api/history                     (req 4.4 via req 4.2)
  - Malformed request body → 422         (req 4.5)
"""

import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

import asyncpg
import httpx

# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/supachat_test"),
)

# Marker applied to all tests that need a real Postgres instance
requires_db = pytest.mark.skipif(
    os.environ.get("TEST_DATABASE_URL") is None and os.environ.get("DATABASE_URL") is None,
    reason="No TEST_DATABASE_URL or DATABASE_URL set; skipping DB-dependent tests",
)

# Minimal schema needed for integration tests
_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    topic        TEXT NOT NULL,
    author       TEXT,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS article_views (
    id           SERIAL PRIMARY KEY,
    article_id   INT REFERENCES articles(id),
    viewed_date  DATE NOT NULL,
    view_count   INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS article_engagement (
    id           SERIAL PRIMARY KEY,
    article_id   INT REFERENCES articles(id),
    event_date   DATE NOT NULL,
    likes        INT DEFAULT 0,
    comments     INT DEFAULT 0,
    shares       INT DEFAULT 0
);
"""

_SEED_SQL = """
INSERT INTO articles (title, topic, author, published_at)
VALUES
    ('Intro to Python', 'Python', 'Alice', NOW() - INTERVAL '10 days'),
    ('DevOps Basics',   'DevOps', 'Bob',   NOW() - INTERVAL '5 days')
ON CONFLICT DO NOTHING;

INSERT INTO article_views (article_id, viewed_date, view_count)
SELECT id, CURRENT_DATE - INTERVAL '1 day', 100
FROM articles
ON CONFLICT DO NOTHING;
"""

_TEARDOWN_SQL = """
DROP TABLE IF EXISTS article_engagement;
DROP TABLE IF EXISTS article_views;
DROP TABLE IF EXISTS articles;
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """Create a real Postgres pool, set up schema, yield, then tear down."""
    try:
        pool = await asyncpg.create_pool(TEST_DB_URL, min_size=1, max_size=3)
    except (OSError, asyncpg.PostgresError, Exception) as exc:
        pytest.skip(f"Postgres unavailable at {TEST_DB_URL}: {exc}")
        return
    async with pool.acquire() as conn:
        await conn.execute(_SETUP_SQL)
        await conn.execute(_SEED_SQL)
    yield pool
    async with pool.acquire() as conn:
        await conn.execute(_TEARDOWN_SQL)
    await pool.close()


@pytest_asyncio.fixture
async def client(db_pool, tmp_path):
    """
    Spin up the FastAPI app with:
      - the real DB pool injected
      - LLM calls mocked
      - a temp SQLite history DB
    """
    history_db = str(tmp_path / "test_history.db")

    import app.db as db_module
    import app.history as history_module

    original_pool = db_module._pool
    original_db_path = history_module.DB_PATH

    db_module._pool = db_pool
    history_module.DB_PATH = history_db

    from app.history import init_history_db
    await init_history_db()

    from app.main import app as fastapi_app
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    db_module._pool = original_pool
    history_module.DB_PATH = original_db_path


@pytest_asyncio.fixture
async def no_db_client(tmp_path):
    """
    FastAPI client with NO real DB pool (pool=None) — for testing error paths
    and endpoints that don't touch Postgres (e.g. /health, malformed bodies).
    """
    history_db = str(tmp_path / "test_history_nopool.db")

    import app.db as db_module
    import app.history as history_module

    original_pool = db_module._pool
    original_db_path = history_module.DB_PATH

    db_module._pool = None
    history_module.DB_PATH = history_db

    from app.history import init_history_db
    await init_history_db()

    from app.main import app as fastapi_app
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    db_module._pool = original_pool
    history_module.DB_PATH = original_db_path


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_llm(sql: str = "SELECT id, title FROM articles LIMIT 5;"):
    """Return a context manager that patches generate_sql to return `sql`."""
    return patch("app.main.generate_sql", new=AsyncMock(return_value=sql))


def _mock_llm_summary(summary: str = "Here are the results."):
    """Patch the internal _call_llm used for summary generation."""
    return patch("app.llm._call_llm", new=AsyncMock(return_value=summary))


# ---------------------------------------------------------------------------
# GET /health  (req 4.3)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_ok(no_db_client):
    response = await no_db_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/query — success path  (req 4.1, 4.2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@requires_db
async def test_query_success_returns_structured_response(client, db_pool):
    """End-to-end: NL query → mock SQL → real DB → formatted QueryResponse."""
    sql = "SELECT id, title FROM articles LIMIT 5;"
    with _mock_llm(sql), _mock_llm_summary("Found 2 articles."):
        response = await client.post(
            "/api/query", json={"query": "Show me all articles", "session_id": "test-1"}
        )

    assert response.status_code == 200
    body = response.json()

    # req 4.2 — response shape
    assert "summary" in body
    assert "sql" in body
    assert "columns" in body
    assert "rows" in body
    assert "chart_type" in body
    assert "chart_data" in body
    assert "query_id" in body
    assert "timestamp" in body

    assert body["sql"] == sql
    assert isinstance(body["columns"], list)
    assert isinstance(body["rows"], list)
    assert body["chart_type"] in ("line", "bar", "pie", "none")


@pytest.mark.asyncio
@requires_db
async def test_query_returns_real_db_rows(client, db_pool):
    """Rows returned match what's actually in the test DB."""
    sql = "SELECT title FROM articles ORDER BY id;"
    with _mock_llm(sql), _mock_llm_summary("Two articles found."):
        response = await client.post("/api/query", json={"query": "list articles"})

    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["title"]
    titles = [row[0] for row in body["rows"]]
    assert "Intro to Python" in titles
    assert "DevOps Basics" in titles


@pytest.mark.asyncio
@requires_db
async def test_query_empty_result_returns_no_data_summary(client):
    """A query that returns 0 rows gets chart_type 'none' and a no-data summary."""
    sql = "SELECT * FROM articles WHERE id = -999;"
    with _mock_llm(sql):
        response = await client.post("/api/query", json={"query": "find nonexistent article"})

    assert response.status_code == 200
    body = response.json()
    assert body["rows"] == []
    assert body["chart_type"] == "none"
    assert "no data" in body["summary"].lower()


# ---------------------------------------------------------------------------
# POST /api/query — error scenarios  (req 4.5)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_query_invalid_sql_returns_422(no_db_client):
    """When generate_sql raises InvalidSQLError, the endpoint returns 422."""
    from app.llm import InvalidSQLError

    with patch(
        "app.main.generate_sql",
        new=AsyncMock(side_effect=InvalidSQLError("Failed to generate valid SQL after 2 attempts")),
    ):
        response = await no_db_client.post("/api/query", json={"query": "gibberish $$$ query"})

    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_query_db_down_returns_503(no_db_client):
    """When the DB pool is None (simulating DB down), the endpoint returns 503."""
    sql = "SELECT 1;"
    with _mock_llm(sql):
        response = await no_db_client.post("/api/query", json={"query": "anything"})

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_query_llm_runtime_error_returns_503(no_db_client):
    """When the LLM service is unavailable (RuntimeError), the endpoint returns 503."""
    with patch(
        "app.main.generate_sql",
        new=AsyncMock(side_effect=RuntimeError("AI service timeout")),
    ):
        response = await no_db_client.post("/api/query", json={"query": "test"})

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_query_malformed_body_returns_422(no_db_client):
    """Missing required 'query' field triggers FastAPI validation → 422 (req 4.5)."""
    response = await no_db_client.post("/api/query", json={"not_query": "oops"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_empty_string_body_returns_422(no_db_client):
    """Sending a non-JSON body returns 422."""
    response = await no_db_client.post(
        "/api/query",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/history  (req 4.4)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_history_empty_on_fresh_db(no_db_client):
    """GET /api/history returns an empty list when no queries have been made."""
    response = await no_db_client.get("/api/history")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@requires_db
async def test_history_records_saved_after_query(client, db_pool):
    """After a successful query, GET /api/history returns that record."""
    sql = "SELECT id, title FROM articles LIMIT 1;"
    with _mock_llm(sql), _mock_llm_summary("One article."):
        post_resp = await client.post(
            "/api/query", json={"query": "get one article", "session_id": "hist-test"}
        )
    assert post_resp.status_code == 200
    query_id = post_resp.json()["query_id"]

    history_resp = await client.get("/api/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    ids = [r["query_id"] for r in history]
    assert query_id in ids


@pytest.mark.asyncio
@requires_db
async def test_history_response_shape(client, db_pool):
    """Each history record has the same shape as QueryResponse (req 4.2)."""
    sql = "SELECT topic FROM articles LIMIT 1;"
    with _mock_llm(sql), _mock_llm_summary("One topic."):
        await client.post("/api/query", json={"query": "get a topic"})

    response = await client.get("/api/history")
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 1

    record = records[0]
    for field in ("summary", "sql", "columns", "rows", "chart_type", "chart_data", "query_id", "timestamp"):
        assert field in record, f"Missing field '{field}' in history record"
