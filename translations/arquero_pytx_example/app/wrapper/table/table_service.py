"""Thin orchestration layer for table operations.

Delegates all computation to the injected TableProcessor. Contains no
business logic — only request parsing and response formatting.
Part of the immutable wrapper layer.
"""
from __future__ import annotations

from typing import Any


def _shape(rows: list[dict]) -> dict:
    """Wrap rows in the standard response envelope."""
    col_names = list(rows[0].keys()) if rows else []
    return {
        "rows": rows,
        "numRows": len(rows),
        "numCols": len(col_names),
        "columnNames": col_names,
    }


class TableService:
    """Thin orchestration service — delegates to the processor."""

    def __init__(self, processor) -> None:
        self._processor = processor

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def from_json(self, body: dict[str, Any]) -> dict:
        data = list(body.get("data") or [])
        return _shape(self._processor.from_json(data))

    def from_csv(self, body: dict[str, Any]) -> dict:
        csv_str = body.get("csv", "")
        options = body.get("options") or {}
        delimiter = options.get("delimiter", ",")
        return _shape(self._processor.from_csv(csv_str, delimiter))

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    def select(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = list(body.get("columns") or [])
        result = self._processor.select(rows, columns)
        return {"rows": result, "numRows": len(result), "numCols": len(columns), "columnNames": columns}

    def rename(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        mapping = body.get("columns") or {}
        return _shape(self._processor.rename(rows, mapping))

    def relocate(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns") or []
        options = body.get("options") or {}
        result = self._processor.relocate(rows, columns, options)
        if not result:
            return _shape(result)
        order = list(result[0].keys())
        return {"rows": result, "numRows": len(result), "numCols": len(order), "columnNames": order}

    def derive(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns") or {}
        return _shape(self._processor.derive(rows, columns))

    def assign(self, body: dict[str, Any]) -> dict:
        left = list(body.get("data") or [])
        other = list(body.get("other") or [])
        return _shape(self._processor.assign(left, other))

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------

    def filter_rows(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        expr = body.get("expr", "")
        return _shape(self._processor.filter_rows(rows, expr))

    def orderby(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        exprs = body.get("exprs") or []
        return _shape(self._processor.orderby(rows, exprs))

    def slice_rows(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        start = body.get("start") or 0
        end = body.get("end")
        return _shape(self._processor.slice_rows(rows, start, end))

    def sample(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        n = body.get("n") or 1
        return _shape(self._processor.sample(rows, n))

    def dedupe(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns")
        return _shape(self._processor.dedupe(rows, columns))

    def impute(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        values = body.get("values") or {}
        return _shape(self._processor.impute(rows, values))

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def rollup(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        rollup_def = body.get("rollup") or {}
        return _shape(self._processor.rollup(rows, rollup_def))

    def groupby_rollup(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        by = body.get("by") or []
        rollup_def = body.get("rollup") or {}
        return _shape(self._processor.groupby_rollup(rows, by, rollup_def))

    # ------------------------------------------------------------------
    # Reshaping
    # ------------------------------------------------------------------

    def fold(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns") or []
        options = body.get("options") or {}
        return _shape(self._processor.fold(rows, columns, options))

    def pivot(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        on = body.get("on") or []
        values = body.get("values") or []
        options = body.get("options") or {}
        return _shape(self._processor.pivot(rows, on, values, options))

    def spread(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns") or []
        options = body.get("options") or {}
        return _shape(self._processor.spread(rows, columns, options))

    def unroll(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        columns = body.get("columns") or []
        return _shape(self._processor.unroll(rows, columns))

    # ------------------------------------------------------------------
    # Joins
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_on(on) -> tuple[str, str]:
        """Normalize the 'on' join parameter to (left_col, right_col)."""
        if isinstance(on, list) and len(on) == 2:
            return on[0], on[1]
        return on, on

    def join(self, body: dict[str, Any]) -> dict:
        left = list(body.get("left") or [])
        right = list(body.get("right") or [])
        left_col, right_col = self._parse_on(body.get("on"))
        how = body.get("how", "inner")
        return _shape(self._processor.join(left, right, left_col, right_col, how))

    def semijoin(self, body: dict[str, Any]) -> dict:
        left = list(body.get("left") or [])
        right = list(body.get("right") or [])
        left_col, right_col = self._parse_on(body.get("on"))
        return _shape(self._processor.semijoin(left, right, left_col, right_col))

    def antijoin(self, body: dict[str, Any]) -> dict:
        left = list(body.get("left") or [])
        right = list(body.get("right") or [])
        left_col, right_col = self._parse_on(body.get("on"))
        return _shape(self._processor.antijoin(left, right, left_col, right_col))

    def cross(self, body: dict[str, Any]) -> dict:
        left = list(body.get("left") or [])
        right = list(body.get("right") or [])
        return _shape(self._processor.cross(left, right))

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def union(self, body: dict[str, Any]) -> dict:
        tables = body.get("tables") or []
        return _shape(self._processor.union(tables))

    def intersect(self, body: dict[str, Any]) -> dict:
        tables = body.get("tables") or []
        return _shape(self._processor.intersect(tables))

    def except_op(self, body: dict[str, Any]) -> dict:
        tables = body.get("tables") or []
        return _shape(self._processor.except_op(tables))

    def concat(self, body: dict[str, Any]) -> dict:
        tables = body.get("tables") or []
        return _shape(self._processor.concat(tables))

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------

    def to_csv(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        options = body.get("options") or {}
        delimiter = options.get("delimiter", ",")
        return {"csv": self._processor.to_csv(rows, delimiter)}

    def to_markdown(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        return {"markdown": self._processor.to_markdown(rows)}

    def to_json(self, body: dict[str, Any]) -> dict:
        rows = list(body.get("data") or [])
        return {"json": self._processor.to_json(rows)}
