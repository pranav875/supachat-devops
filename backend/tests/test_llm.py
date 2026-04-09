"""
Unit tests for backend/app/llm.py (task 5.3).

Tests cover:
  - SQL extraction from LLM response
  - Relative date resolution (today's date injected into prompt)
  - Retry on invalid SQL (first attempt bad, second attempt good)
  - Failure after two bad attempts raises InvalidSQLError
  - Provider selection (OpenAI vs Anthropic)
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date


# ---------------------------------------------------------------------------
# _extract_sql tests
# ---------------------------------------------------------------------------

def test_extract_sql_standard_block():
    from app.llm import _extract_sql
    text = "Here is the query:\n```sql\nSELECT 1;\n```"
    assert _extract_sql(text) == "SELECT 1;"


def test_extract_sql_no_language_tag():
    from app.llm import _extract_sql
    text = "```\nSELECT * FROM articles;\n```"
    assert _extract_sql(text) == "SELECT * FROM articles;"


def test_extract_sql_no_block_raises():
    from app.llm import _extract_sql
    with pytest.raises(ValueError, match="No SQL block found"):
        _extract_sql("I cannot generate SQL for that.")


def test_extract_sql_empty_block_raises():
    from app.llm import _extract_sql
    with pytest.raises(ValueError, match="SQL block is empty"):
        _extract_sql("```sql\n   \n```")


def test_extract_sql_multiline():
    from app.llm import _extract_sql
    sql = "SELECT a.topic, SUM(av.view_count)\nFROM articles a\nJOIN article_views av ON av.article_id = a.id\nGROUP BY a.topic;"
    text = f"```sql\n{sql}\n```"
    assert _extract_sql(text) == sql


# ---------------------------------------------------------------------------
# _build_system_prompt — relative date injection (req 3.4)
# ---------------------------------------------------------------------------

def test_system_prompt_contains_today():
    from app.llm import _build_system_prompt
    today = "2026-08-04"
    prompt = _build_system_prompt(today)
    assert "2026-08-04" in prompt


def test_system_prompt_contains_schema():
    from app.llm import _build_system_prompt
    prompt = _build_system_prompt("2026-08-04")
    assert "articles" in prompt
    assert "article_views" in prompt
    assert "article_engagement" in prompt


def test_system_prompt_contains_few_shot_examples():
    from app.llm import _build_system_prompt
    prompt = _build_system_prompt("2026-08-04")
    assert "```sql" in prompt


# ---------------------------------------------------------------------------
# generate_sql — success path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_sql_success_openai():
    """generate_sql returns extracted SQL on first attempt (OpenAI path)."""
    good_response = "```sql\nSELECT topic, COUNT(*) FROM articles GROUP BY topic;\n```"
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": ""}):
        with patch("app.llm._call_openai", new=AsyncMock(return_value=good_response)):
            from app.llm import generate_sql
            sql = await generate_sql("How many articles per topic?")
    assert "SELECT" in sql.upper()
    assert "articles" in sql


@pytest.mark.asyncio
async def test_generate_sql_success_anthropic():
    """generate_sql uses Anthropic when only ANTHROPIC_API_KEY is set."""
    good_response = "```sql\nSELECT title FROM articles LIMIT 5;\n```"
    with patch.dict("os.environ", {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": "sk-ant-test"}):
        with patch("app.llm._call_anthropic", new=AsyncMock(return_value=good_response)):
            from app.llm import generate_sql
            sql = await generate_sql("Show me 5 articles")
    assert "SELECT" in sql.upper()


# ---------------------------------------------------------------------------
# generate_sql — retry logic (req 3.3)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_sql_retries_on_bad_first_response():
    """If first LLM call returns no SQL block, a second call is made."""
    bad_response = "I'm sorry, I cannot help with that."
    good_response = "```sql\nSELECT 1;\n```"

    call_count = 0

    async def mock_call_llm(system, user):
        nonlocal call_count
        call_count += 1
        return bad_response if call_count == 1 else good_response

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        with patch("app.llm._call_llm", new=mock_call_llm):
            from app.llm import generate_sql
            sql = await generate_sql("anything")

    assert call_count == 2
    assert sql == "SELECT 1;"


@pytest.mark.asyncio
async def test_generate_sql_raises_after_two_failures():
    """After two failed attempts, InvalidSQLError is raised (req 3.3)."""
    bad_response = "No SQL here."

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        with patch("app.llm._call_llm", new=AsyncMock(return_value=bad_response)):
            from app.llm import generate_sql, InvalidSQLError
            with pytest.raises(InvalidSQLError, match="Failed to generate valid SQL after 2 attempts"):
                await generate_sql("something unanswerable")


@pytest.mark.asyncio
async def test_generate_sql_retry_message_includes_error():
    """The retry prompt includes the error from the first attempt."""
    bad_response = "No SQL here."
    good_response = "```sql\nSELECT 1;\n```"
    captured_messages = []

    call_count = 0

    async def mock_call_llm(system, user):
        nonlocal call_count
        call_count += 1
        captured_messages.append(user)
        return bad_response if call_count == 1 else good_response

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        with patch("app.llm._call_llm", new=mock_call_llm):
            from app.llm import generate_sql
            await generate_sql("my query")

    # Second call's user message should reference the previous error
    assert len(captured_messages) == 2
    assert "SQL block" in captured_messages[1] or "Error" in captured_messages[1]


# ---------------------------------------------------------------------------
# generate_sql — no provider configured
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_sql_no_provider_raises():
    """RuntimeError is raised when neither API key is set."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": "", "GEMINI_API_KEY": "", "GROQ_API_KEY": ""}):
        from app.llm import generate_sql
        with pytest.raises(RuntimeError, match="No LLM provider configured"):
            await generate_sql("test query")
