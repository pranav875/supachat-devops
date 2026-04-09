"""
Result formatter: detects chart type and shapes data for Recharts.

Chart type detection rules (design doc §2.6):
  - 2 columns, col[0] is date-like, col[1] is numeric  → "line"
  - 2 columns, col[0] is category (str), col[1] is numeric → "bar"
  - 2 columns, col[0] is label, col[1] looks like share/pct  → "pie"
  - anything else                                            → "none"
"""

from __future__ import annotations

import re
from typing import Any

# Regex that matches common ISO date / date-like strings (YYYY-MM-DD, YYYY/MM/DD, etc.)
_DATE_RE = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}")

_SHARE_KEYWORDS = {"share", "pct", "percent", "percentage", "ratio", "proportion"}


def _is_date_value(value: Any) -> bool:
    """Return True if the value looks like a date."""
    if value is None:
        return False
    return bool(_DATE_RE.match(str(value)))


def _is_numeric(value: Any) -> bool:
    """Return True if the value is an int or float (not bool)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _column_looks_like_share(col_name: str) -> bool:
    """Return True if the column name suggests a share/percentage."""
    return any(kw in col_name.lower() for kw in _SHARE_KEYWORDS)


def _detect_chart_type(columns: list[str], rows: list[list[Any]]) -> str:
    """Inspect columns and the first data row to pick a chart type."""
    if len(columns) != 2 or not rows:
        return "none"

    first_row = rows[0]
    if len(first_row) < 2:
        return "none"

    col0_val, col1_val = first_row[0], first_row[1]

    # col[1] must be numeric for all chart types
    if not _is_numeric(col1_val):
        return "none"

    # date + numeric → line
    if _is_date_value(col0_val):
        return "line"

    # label + share keyword → pie
    if _column_looks_like_share(columns[1]):
        return "pie"

    # category (string) + numeric → bar
    if isinstance(col0_val, str):
        return "bar"

    return "none"


def _shape_chart_data(
    chart_type: str, columns: list[str], rows: list[list[Any]]
) -> list[dict[str, Any]]:
    """Convert raw rows into Recharts-compatible data."""
    if chart_type == "none" or not rows:
        return []

    name_col, value_col = columns[0], columns[1]

    if chart_type in ("line", "bar"):
        return [{"name": str(row[0]), value_col: row[1]} for row in rows]

    if chart_type == "pie":
        return [{"name": str(row[0]), "value": row[1]} for row in rows]

    return []


def format_results(columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    """
    Given query result columns and rows, return a dict with:
      - chart_type: "line" | "bar" | "pie" | "none"
      - chart_data: Recharts-compatible list of dicts
    """
    if not columns or not rows:
        return {"chart_type": "none", "chart_data": []}

    chart_type = _detect_chart_type(columns, rows)
    chart_data = _shape_chart_data(chart_type, columns, rows)

    return {"chart_type": chart_type, "chart_data": chart_data}
