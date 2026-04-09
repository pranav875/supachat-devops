import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from app.db import close_pool, execute_read_query, init_pool
from app.formatter import format_results
from app.history import get_history, init_history_db, save_query, delete_history_record, clear_history
from app.llm import InvalidSQLError, generate_sql
from app.schemas import HistoryRecord, QueryRequest, QueryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await init_history_db()
    yield
    await close_pool()


app = FastAPI(title="SupaChat API", lifespan=lifespan)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    query_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Step 1: Generate SQL from natural language (req 3.1, 3.3)
    try:
        sql = await generate_sql(request.query)
    except InvalidSQLError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Step 2: Execute query via MCP / db layer (req 3.2, 4.5)
    # execute_read_query already raises 503 on DB errors
    result = await execute_read_query(sql)
    columns: list = result["columns"]
    rows: list = result["rows"]

    # Step 3: Format results and detect chart type (req 3.2)
    formatted = format_results(columns, rows)

    # Step 4: Generate text summary via LLM
    if rows:
        summary_prompt = (
            f"The user asked: {request.query!r}\n"
            f"The SQL query returned {len(rows)} row(s) with columns {columns}.\n"
            f"First few rows: {rows[:5]}\n"
            "Write a concise 1-2 sentence plain-English summary of the results."
        )
        try:
            from app.llm import _call_llm
            summary = await _call_llm(
                "You are a helpful data analyst. Summarize query results concisely.",
                summary_prompt,
            )
        except Exception:
            summary = f"Query returned {len(rows)} row(s)."
    else:
        summary = "No data found for your query."

    # Step 5: Persist to history (req 4.4)
    record = HistoryRecord(
        query_id=query_id,
        session_id=request.session_id,
        nl_query=request.query,
        sql=sql,
        summary=summary,
        columns=columns,
        rows=rows,
        chart_type=formatted["chart_type"],
        chart_data=formatted["chart_data"],
        timestamp=timestamp,
        error=None,
    )
    await save_query(record)

    return QueryResponse(
        summary=summary,
        sql=sql,
        columns=columns,
        rows=rows,
        chart_type=formatted["chart_type"],
        chart_data=formatted["chart_data"],
        query_id=query_id,
        timestamp=timestamp.isoformat(),
    )


@app.get("/api/history", response_model=list[QueryResponse])
async def history():
    limit = int(os.getenv("HISTORY_LIMIT", "50"))
    records = await get_history(limit)
    return [
        QueryResponse(
            summary=r.summary,
            sql=r.sql,
            columns=r.columns,
            rows=r.rows,
            chart_type=r.chart_type,
            chart_data=r.chart_data,
            query_id=r.query_id,
            timestamp=r.timestamp.isoformat(),
        )
        for r in records
    ]


@app.delete("/api/history")
async def delete_all_history():
    count = await clear_history()
    return {"deleted": count}


@app.delete("/api/history/{query_id}")
async def delete_history_item(query_id: str):
    deleted = await delete_history_record(query_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": True}
