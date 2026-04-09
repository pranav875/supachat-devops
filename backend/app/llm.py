"""
LLM integration for SupaChat — natural language to SQL translation.

Supports OpenAI, Anthropic, Google Gemini, and Groq providers.
Provider selection priority: OPENAI_API_KEY → ANTHROPIC_API_KEY → GEMINI_API_KEY → GROQ_API_KEY.
"""

import os
import re
from datetime import date

# ---------------------------------------------------------------------------
# Schema context (mirrors mcp_server._SCHEMA_INFO for prompt building)
# ---------------------------------------------------------------------------

_SCHEMA_TEXT = """\
Tables:
  articles(id SERIAL PK, title TEXT, topic TEXT, author TEXT, published_at TIMESTAMPTZ)
  article_views(id SERIAL PK, article_id INT FK->articles.id, viewed_date DATE, view_count INT)
  article_engagement(id SERIAL PK, article_id INT FK->articles.id, event_date DATE,
                     likes INT, comments INT, shares INT)
"""

_FEW_SHOT_EXAMPLES = """\
Q: How many views did each topic get in the last 30 days?
A:
```sql
SELECT a.topic, SUM(av.view_count) AS total_views
FROM articles a
JOIN article_views av ON av.article_id = a.id
WHERE av.viewed_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.topic
ORDER BY total_views DESC;
```

Q: Which article had the most likes last week?
A:
```sql
SELECT a.title, SUM(ae.likes) AS total_likes
FROM articles a
JOIN article_engagement ae ON ae.article_id = a.id
WHERE ae.event_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY a.title
ORDER BY total_likes DESC
LIMIT 1;
```
"""


def _build_system_prompt(today: str) -> str:
    return (
        "You are a PostgreSQL expert. Convert the user's natural language question into a "
        "single valid PostgreSQL SELECT statement. Return ONLY the SQL inside a ```sql ... ``` "
        "code block — no explanation, no commentary.\n\n"
        f"Today's date: {today}\n\n"
        "Schema:\n"
        f"{_SCHEMA_TEXT}\n"
        "Examples:\n"
        f"{_FEW_SHOT_EXAMPLES}"
    )


# ---------------------------------------------------------------------------
# SQL extraction
# ---------------------------------------------------------------------------

_SQL_BLOCK_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_sql(text: str) -> str:
    """
    Parse the LLM response and return the SQL string.
    Raises ValueError if no SQL block is found.
    """
    match = _SQL_BLOCK_RE.search(text)
    if not match:
        raise ValueError(f"No SQL block found in LLM response: {text!r}")
    sql = match.group(1).strip()
    if not sql:
        raise ValueError("SQL block is empty in LLM response.")
    return sql


# ---------------------------------------------------------------------------
# Provider-specific call helpers
# ---------------------------------------------------------------------------

async def _call_openai(messages: list[dict], api_key: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content or ""


async def _call_anthropic(messages: list[dict], system: str, api_key: str) -> str:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=system,
        messages=messages,
        temperature=0,
    )
    return response.content[0].text if response.content else ""


async def _call_gemini(system_prompt: str, user_message: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )
    response = await model.generate_content_async(
        user_message,
        generation_config={"temperature": 0},
    )
    return response.text or ""


async def _call_groq(messages: list[dict], api_key: str) -> str:
    # Groq is OpenAI-API-compatible — just swap the base URL
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content or ""


async def _call_llm(system_prompt: str, user_message: str) -> str:
    """Dispatch to the configured LLM provider and return the raw text response."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    if openai_key:
        return await _call_openai(messages, openai_key)

    if anthropic_key:
        return await _call_anthropic(
            [{"role": "user", "content": user_message}], system_prompt, anthropic_key
        )

    if gemini_key:
        return await _call_gemini(system_prompt, user_message, gemini_key)

    if groq_key:
        return await _call_groq(messages, groq_key)

    raise RuntimeError(
        "No LLM provider configured. "
        "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class InvalidSQLError(ValueError):
    """Raised when the LLM fails to produce valid SQL after all retries."""


async def generate_sql(nl_query: str) -> str:
    """
    Translate a natural language query into a PostgreSQL SELECT statement.

    Attempts up to 2 LLM calls:
      1. Initial attempt with schema context and few-shot examples.
      2. Retry with the previous error appended to the prompt.

    Raises:
        InvalidSQLError: if both attempts fail to produce extractable SQL.
        RuntimeError: if no LLM provider is configured.
    """
    today = date.today().isoformat()
    system_prompt = _build_system_prompt(today)

    # --- First attempt ---
    raw = await _call_llm(system_prompt, nl_query)
    first_err_msg = ""
    try:
        return _extract_sql(raw)
    except ValueError as exc:
        first_err_msg = str(exc)  # capture before exception var is cleared

    # --- Retry with error feedback (req 3.3) ---
    retry_message = (
        f"{nl_query}\n\n"
        f"Your previous response did not contain a valid SQL block. Error: {first_err_msg}\n"
        "Please respond with ONLY a ```sql ... ``` code block."
    )
    raw2 = await _call_llm(system_prompt, retry_message)
    try:
        return _extract_sql(raw2)
    except ValueError as second_err:
        raise InvalidSQLError(
            f"Failed to generate valid SQL after 2 attempts. Last error: {second_err}"
        ) from second_err
