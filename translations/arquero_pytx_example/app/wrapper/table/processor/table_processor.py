"""Abstract base class for table processors.

Defines the interface that implementation classes must fulfill.
Part of the immutable wrapper layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class TableProcessor(ABC):
    """Base class for table processors."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dedup(rows: list[dict]) -> list[dict]:
        """Remove duplicate rows based on all column values."""
        seen: set = set()
        result = []
        for r in rows:
            k = tuple(sorted(r.items()))
            if k not in seen:
                seen.add(k)
                result.append(r)
        return result

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    @abstractmethod
    def from_json(self, data: list[dict]) -> list[dict]:
        """Create table from array of row objects."""

    @abstractmethod
    def from_csv(self, csv_str: str, delimiter: str = ",") -> list[dict]:
        """Parse CSV string into rows."""

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    @abstractmethod
    def select(self, rows: list[dict], columns: list[str]) -> list[dict]:
        """Select columns by name."""

    @abstractmethod
    def rename(self, rows: list[dict], mapping: dict[str, str]) -> list[dict]:
        """Rename columns: {oldName: newName}."""

    @abstractmethod
    def relocate(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        """Reorder columns with before/after options."""

    @abstractmethod
    def derive(self, rows: list[dict], columns: dict[str, str]) -> list[dict]:
        """Compute new columns from expressions."""

    @abstractmethod
    def assign(self, left: list[dict], other: list[dict]) -> list[dict]:
        """Assign columns from a second table (same row count)."""

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------

    @abstractmethod
    def filter_rows(self, rows: list[dict], expr: str) -> list[dict]:
        """Filter rows by predicate expression."""

    @abstractmethod
    def orderby(self, rows: list[dict], exprs: list[str]) -> list[dict]:
        """Sort rows by column names or expressions."""

    @abstractmethod
    def slice_rows(self, rows: list[dict], start: int, end: int | None = None) -> list[dict]:
        """Slice rows from start (inclusive) to end (exclusive)."""

    @abstractmethod
    def sample(self, rows: list[dict], n: int) -> list[dict]:
        """Randomly sample n rows."""

    @abstractmethod
    def dedupe(self, rows: list[dict], columns: list[str] | None = None) -> list[dict]:
        """Remove duplicate rows, optionally based on specific columns."""

    @abstractmethod
    def impute(self, rows: list[dict], values: dict) -> list[dict]:
        """Fill missing values: {colName: fillValue}."""

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    @abstractmethod
    def rollup(self, rows: list[dict], rollup_def: dict) -> list[dict]:
        """Aggregate entire table."""

    @abstractmethod
    def groupby_rollup(self, rows: list[dict], by: list[str], rollup_def: dict) -> list[dict]:
        """Group then aggregate."""

    # ------------------------------------------------------------------
    # Reshaping
    # ------------------------------------------------------------------

    @abstractmethod
    def fold(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        """Melt wide columns to key/value rows."""

    @abstractmethod
    def pivot(self, rows: list[dict], on: list[str], values: list[str], options: dict) -> list[dict]:
        """Pivot key/value rows to wide columns."""

    @abstractmethod
    def spread(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        """Spread an array column into multiple columns."""

    @abstractmethod
    def unroll(self, rows: list[dict], columns: list[str]) -> list[dict]:
        """Expand an array column into multiple rows."""

    # ------------------------------------------------------------------
    # Joins
    # ------------------------------------------------------------------

    @abstractmethod
    def join(self, left: list[dict], right: list[dict], left_col: str, right_col: str, how: str = "inner") -> list[dict]:
        """Join two tables."""

    @abstractmethod
    def semijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        """Keep rows in left that match right."""

    @abstractmethod
    def antijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        """Keep rows in left that do NOT match right."""

    @abstractmethod
    def cross(self, left: list[dict], right: list[dict]) -> list[dict]:
        """Cartesian product of two tables."""

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    @abstractmethod
    def union(self, tables: list[list[dict]]) -> list[dict]:
        """Union of multiple tables (deduped)."""

    @abstractmethod
    def intersect(self, tables: list[list[dict]]) -> list[dict]:
        """Rows present in all tables."""

    @abstractmethod
    def except_op(self, tables: list[list[dict]]) -> list[dict]:
        """Rows in first table not in remaining tables."""

    @abstractmethod
    def concat(self, tables: list[list[dict]]) -> list[dict]:
        """Concatenate tables (no dedup)."""

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------

    @abstractmethod
    def to_csv(self, rows: list[dict], delimiter: str = ",") -> str:
        """Serialize table to CSV string."""

    @abstractmethod
    def to_markdown(self, rows: list[dict]) -> str:
        """Serialize table to Markdown table string."""

    @abstractmethod
    def to_json(self, rows: list[dict]) -> str:
        """Serialize table to JSON string."""
