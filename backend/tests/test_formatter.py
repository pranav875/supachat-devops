"""
Unit tests for backend/app/formatter.py (task 6.2).

Tests cover:
  - Chart type detection: line, bar, pie, none
  - Recharts data shape for each chart type
  - Empty rows → chart_type "none"
  - Empty columns → chart_type "none"
  - Non-numeric second column → "none"
"""

import pytest
from app.formatter import format_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(columns, rows):
    return format_results(columns, rows)


# ---------------------------------------------------------------------------
# Empty / degenerate inputs (req 6.5)
# ---------------------------------------------------------------------------

def test_empty_rows_returns_none():
    result = _result(["viewed_date", "view_count"], [])
    assert result["chart_type"] == "none"
    assert result["chart_data"] == []


def test_empty_columns_returns_none():
    result = _result([], [[]])
    assert result["chart_type"] == "none"
    assert result["chart_data"] == []


def test_single_column_returns_none():
    result = _result(["topic"], [["AI"], ["Python"]])
    assert result["chart_type"] == "none"
    assert result["chart_data"] == []


def test_three_columns_returns_none():
    result = _result(["date", "views", "likes"], [["2024-01-01", 100, 5]])
    assert result["chart_type"] == "none"
    assert result["chart_data"] == []


# ---------------------------------------------------------------------------
# Line chart detection (req 6.1) — date + numeric
# ---------------------------------------------------------------------------

def test_line_chart_detected_for_date_and_numeric():
    columns = ["viewed_date", "view_count"]
    rows = [["2024-01-01", 1200], ["2024-01-02", 980]]
    result = _result(columns, rows)
    assert result["chart_type"] == "line"


def test_line_chart_data_shape():
    columns = ["viewed_date", "view_count"]
    rows = [["2024-01-01", 1200], ["2024-01-02", 980]]
    result = _result(columns, rows)
    assert result["chart_data"] == [
        {"name": "2024-01-01", "view_count": 1200},
        {"name": "2024-01-02", "view_count": 980},
    ]


def test_line_chart_date_with_slash_separator():
    columns = ["date", "count"]
    rows = [["2024/03/15", 50]]
    result = _result(columns, rows)
    assert result["chart_type"] == "line"


# ---------------------------------------------------------------------------
# Bar chart detection (req 6.2) — category string + numeric
# ---------------------------------------------------------------------------

def test_bar_chart_detected_for_category_and_numeric():
    columns = ["topic", "article_count"]
    rows = [["AI", 12], ["Python", 8], ["DevOps", 5]]
    result = _result(columns, rows)
    assert result["chart_type"] == "bar"


def test_bar_chart_data_shape():
    columns = ["topic", "article_count"]
    rows = [["AI", 12], ["Python", 8]]
    result = _result(columns, rows)
    assert result["chart_data"] == [
        {"name": "AI", "article_count": 12},
        {"name": "Python", "article_count": 8},
    ]


# ---------------------------------------------------------------------------
# Pie chart detection (req 6.3) — label + share/percentage column name
# ---------------------------------------------------------------------------

def test_pie_chart_detected_for_share_column():
    columns = ["topic", "share"]
    rows = [["AI", 0.45], ["Python", 0.30], ["DevOps", 0.25]]
    result = _result(columns, rows)
    assert result["chart_type"] == "pie"


def test_pie_chart_detected_for_percent_column():
    columns = ["author", "percent"]
    rows = [["Alice", 60.0], ["Bob", 40.0]]
    result = _result(columns, rows)
    assert result["chart_type"] == "pie"


def test_pie_chart_detected_for_percentage_column():
    columns = ["topic", "percentage"]
    rows = [["AI", 50], ["Other", 50]]
    result = _result(columns, rows)
    assert result["chart_type"] == "pie"


def test_pie_chart_data_shape():
    columns = ["topic", "share"]
    rows = [["AI", 0.45], ["Python", 0.30]]
    result = _result(columns, rows)
    assert result["chart_data"] == [
        {"name": "AI", "value": 0.45},
        {"name": "Python", "value": 0.30},
    ]


# ---------------------------------------------------------------------------
# "none" fallback cases
# ---------------------------------------------------------------------------

def test_none_when_second_column_is_string():
    columns = ["topic", "description"]
    rows = [["AI", "Artificial Intelligence"]]
    result = _result(columns, rows)
    assert result["chart_type"] == "none"
    assert result["chart_data"] == []


def test_none_when_second_column_is_bool():
    columns = ["topic", "is_active"]
    rows = [["AI", True]]
    result = _result(columns, rows)
    assert result["chart_type"] == "none"


def test_none_chart_data_is_empty_list():
    columns = ["a", "b"]
    rows = [["x", "y"]]
    result = _result(columns, rows)
    assert result["chart_data"] == []


# ---------------------------------------------------------------------------
# format_results return structure
# ---------------------------------------------------------------------------

def test_format_results_always_returns_chart_type_and_chart_data_keys():
    result = _result(["viewed_date", "view_count"], [["2024-01-01", 100]])
    assert "chart_type" in result
    assert "chart_data" in result


def test_format_results_line_with_single_row():
    columns = ["viewed_date", "views"]
    rows = [["2024-06-01", 500]]
    result = _result(columns, rows)
    assert result["chart_type"] == "line"
    assert len(result["chart_data"]) == 1
    assert result["chart_data"][0] == {"name": "2024-06-01", "views": 500}
