from datetime import datetime
from typing import Any

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str = ""


class QueryResponse(BaseModel):
    summary: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    chart_type: str  # "line" | "bar" | "pie" | "none"
    chart_data: list[dict[str, Any]]
    query_id: str
    timestamp: str


class HistoryRecord(BaseModel):
    query_id: str
    session_id: str
    nl_query: str
    sql: str
    summary: str
    columns: list[str]
    rows: list[list[Any]]
    chart_type: str
    chart_data: list[dict[str, Any]]
    timestamp: datetime
    error: str | None = None
