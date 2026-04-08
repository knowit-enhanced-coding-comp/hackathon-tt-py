"""Stub table processor — returns empty/passthrough values for all operations.

This is the example skeleton: it has the correct interface but no real
processing logic. Tests will fail on value assertions but all endpoints
will run without errors. Replace this file with a real implementation.
"""
from __future__ import annotations

from app.wrapper.table.processor.table_processor import TableProcessor


class DefaultTableProcessor(TableProcessor):
    """Stub table processor — no real implementation."""

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def from_json(self, data: list[dict]) -> list[dict]:
        return list(data)

    def from_csv(self, csv_str: str, delimiter: str = ",") -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    def select(self, rows: list[dict], columns: list[str]) -> list[dict]:
        return rows

    def rename(self, rows: list[dict], mapping: dict[str, str]) -> list[dict]:
        return rows

    def relocate(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        return rows

    def derive(self, rows: list[dict], columns: dict[str, str]) -> list[dict]:
        return rows

    def assign(self, left: list[dict], other: list[dict]) -> list[dict]:
        return left

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------

    def filter_rows(self, rows: list[dict], expr: str) -> list[dict]:
        return rows

    def orderby(self, rows: list[dict], exprs: list[str]) -> list[dict]:
        return rows

    def slice_rows(self, rows: list[dict], start: int, end: int | None = None) -> list[dict]:
        return rows

    def sample(self, rows: list[dict], n: int) -> list[dict]:
        return rows[:n] if rows else []

    def dedupe(self, rows: list[dict], columns: list[str] | None = None) -> list[dict]:
        return rows

    def impute(self, rows: list[dict], values: dict) -> list[dict]:
        return rows

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def rollup(self, rows: list[dict], rollup_def: dict) -> list[dict]:
        return [{k: None for k in rollup_def}]

    def groupby_rollup(self, rows: list[dict], by: list[str], rollup_def: dict) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Reshaping
    # ------------------------------------------------------------------

    def fold(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        return []

    def pivot(self, rows: list[dict], on: list[str], values: list[str], options: dict) -> list[dict]:
        return []

    def spread(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        return rows

    def unroll(self, rows: list[dict], columns: list[str]) -> list[dict]:
        return rows

    # ------------------------------------------------------------------
    # Joins
    # ------------------------------------------------------------------

    def join(self, left: list[dict], right: list[dict], left_col: str, right_col: str, how: str = "inner") -> list[dict]:
        return []

    def semijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        return []

    def antijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        return []

    def cross(self, left: list[dict], right: list[dict]) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def union(self, tables: list[list[dict]]) -> list[dict]:
        return []

    def intersect(self, tables: list[list[dict]]) -> list[dict]:
        return []

    def except_op(self, tables: list[list[dict]]) -> list[dict]:
        return []

    def concat(self, tables: list[list[dict]]) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------

    def to_csv(self, rows: list[dict], delimiter: str = ",") -> str:
        return ""

    def to_markdown(self, rows: list[dict]) -> str:
        return ""

    def to_json(self, rows: list[dict]) -> str:
        return "[]"
