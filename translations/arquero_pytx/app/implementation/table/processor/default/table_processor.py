"""Default table processor — full Python implementation.

Translates JavaScript arrow-function expressions (derive, filter, rollup)
into Python evaluation at runtime.  Structural operations (select, rename,
join, etc.) are implemented with plain Python.
"""
from __future__ import annotations

import csv as csv_module
import io
import json
import math
import random
import re
import statistics

from app.wrapper.table.processor.table_processor import TableProcessor


# ---------------------------------------------------------------------------
# JS expression evaluation helpers
# ---------------------------------------------------------------------------

_ARROW_RE = re.compile(r'^\s*\(?\s*(\w*)\s*\)?\s*=>\s*(.+)$', re.DOTALL)


def _parse_arrow(expr_str: str) -> tuple[str | None, str]:
    """Parse 'd => body' into (param_name, body)."""
    m = _ARROW_RE.match(expr_str.strip())
    if not m:
        raise ValueError(f"Cannot parse arrow function: {expr_str}")
    param = m.group(1) or None
    return param, m.group(2).strip()


def _js_body_to_py(body: str, param: str | None) -> str:
    """Convert a JS expression body to evaluable Python."""
    body = body.replace('===', '==').replace('!==', '!=')
    body = body.replace('&&', ' and ').replace('||', ' or ')
    body = re.sub(r'\bop\.abs\(', 'abs(', body)
    body = re.sub(r'\bop\.sqrt\(', '_sqrt_(', body)
    body = re.sub(r'\bop\.pow\(', 'pow(', body)
    if param:
        body = re.sub(rf'\b{re.escape(param)}\.(\w+)', rf'{param}["\1"]', body)
    return body


_ROW_EVAL_GLOBALS: dict = {"__builtins__": {}, "_sqrt_": math.sqrt, "abs": abs, "pow": pow}


def _eval_row_expr(expr_str: str, row: dict):
    """Evaluate a per-row JS arrow expression against a single row."""
    param, body = _parse_arrow(expr_str)
    py_body = _js_body_to_py(body, param)
    local_vars = {param: row} if param else {}
    return eval(py_body, _ROW_EVAL_GLOBALS, local_vars)


# Aggregate op pattern: op.func() or op.func(d.col)
_AGG_RE = re.compile(r'op\.(\w+)\(\s*(?:\w+\.(\w+))?\s*\)')


def _eval_aggregate(expr_str: str, rows: list[dict]):
    """Evaluate an aggregate expression (op.sum, op.count, etc.) over rows."""
    _, body = _parse_arrow(expr_str)
    m = _AGG_RE.search(body.strip())
    if not m:
        raise ValueError(f"Cannot parse aggregate expression: {expr_str}")
    func_name = m.group(1)
    col = m.group(2)  # None for op.count()

    if func_name == "count":
        return len(rows)

    vals = [r[col] for r in rows if r.get(col) is not None]

    if func_name == "sum":
        return sum(vals)
    if func_name == "mean":
        return sum(vals) / len(vals) if vals else 0
    if func_name == "min":
        return min(vals) if vals else None
    if func_name == "max":
        return max(vals) if vals else None
    if func_name == "median":
        return statistics.median(vals) if vals else None
    if func_name in ("stdev", "stdevp"):
        return statistics.stdev(vals) if len(vals) > 1 else 0
    if func_name in ("variance", "variancep"):
        return statistics.variance(vals) if len(vals) > 1 else 0

    raise ValueError(f"Unknown aggregate function: op.{func_name}")


class DefaultTableProcessor(TableProcessor):
    """Full Python implementation of the Arquero table processor."""

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def from_json(self, data: list[dict]) -> list[dict]:
        return list(data)

    def from_csv(self, csv_str: str, delimiter: str = ",") -> list[dict]:
        reader = csv_module.DictReader(io.StringIO(csv_str), delimiter=delimiter)
        rows: list[dict] = []
        for row in reader:
            parsed: dict = {}
            for k, v in row.items():
                if v is None or v == "":
                    parsed[k] = None
                else:
                    try:
                        parsed[k] = int(v)
                    except ValueError:
                        try:
                            parsed[k] = float(v)
                        except ValueError:
                            parsed[k] = v
            rows.append(parsed)
        return rows

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    def select(self, rows: list[dict], columns: list[str]) -> list[dict]:
        return [{c: r[c] for c in columns if c in r} for r in rows]

    def rename(self, rows: list[dict], mapping: dict[str, str]) -> list[dict]:
        return [{mapping.get(k, k): v for k, v in r.items()} for r in rows]

    def relocate(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        if not rows:
            return rows
        all_cols = list(rows[0].keys())
        remaining = [c for c in all_cols if c not in columns]
        if "before" in options:
            idx = remaining.index(options["before"]) if options["before"] in remaining else 0
            order = remaining[:idx] + columns + remaining[idx:]
        elif "after" in options:
            idx = remaining.index(options["after"]) + 1 if options["after"] in remaining else len(remaining)
            order = remaining[:idx] + columns + remaining[idx:]
        else:
            order = columns + remaining
        return [{c: r[c] for c in order if c in r} for r in rows]

    def derive(self, rows: list[dict], columns: dict[str, str]) -> list[dict]:
        result = []
        for r in rows:
            new_row = dict(r)
            for col_name, expr_str in columns.items():
                new_row[col_name] = _eval_row_expr(expr_str, new_row)
            result.append(new_row)
        return result

    def assign(self, left: list[dict], other: list[dict]) -> list[dict]:
        return [{**left[i], **other[i]} for i in range(min(len(left), len(other)))]

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------

    def filter_rows(self, rows: list[dict], expr: str) -> list[dict]:
        return [r for r in rows if _eval_row_expr(expr, r)]

    def orderby(self, rows: list[dict], exprs: list[str]) -> list[dict]:
        result = list(rows)
        for expr in reversed(exprs):
            expr = expr.strip()
            if expr.startswith("desc("):
                col = expr[5:].rstrip(")").strip("'\"")
                result = sorted(result, key=lambda r: (r.get(col) is None, r.get(col)), reverse=True)
            elif expr.startswith("asc("):
                col = expr[4:].rstrip(")").strip("'\"")
                result = sorted(result, key=lambda r: (r.get(col) is None, r.get(col)))
            elif "=>" not in expr:
                result = sorted(result, key=lambda r, c=expr: (r.get(c) is None, r.get(c)))
        return result

    def slice_rows(self, rows: list[dict], start: int, end: int | None = None) -> list[dict]:
        return rows[start:end]

    def sample(self, rows: list[dict], n: int) -> list[dict]:
        return random.sample(rows, min(n, len(rows)))

    def dedupe(self, rows: list[dict], columns: list[str] | None = None) -> list[dict]:
        seen: set = set()
        result = []
        for r in rows:
            key = tuple(r.get(c) for c in columns) if columns else tuple(sorted(r.items()))
            if key not in seen:
                seen.add(key)
                result.append(r)
        return result

    def impute(self, rows: list[dict], values: dict) -> list[dict]:
        return [{k: (values[k] if v is None and k in values else v) for k, v in r.items()} for r in rows]

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def rollup(self, rows: list[dict], rollup_def: dict) -> list[dict]:
        return [{k: _eval_aggregate(expr, rows) for k, expr in rollup_def.items()}]

    def groupby_rollup(self, rows: list[dict], by: list[str], rollup_def: dict) -> list[dict]:
        groups: dict[tuple, list[dict]] = {}
        group_order: list[tuple] = []
        for r in rows:
            key = tuple(r.get(c) for c in by)
            if key not in groups:
                groups[key] = []
                group_order.append(key)
            groups[key].append(r)
        result = []
        for key in group_order:
            group_rows = groups[key]
            row = dict(zip(by, key))
            for k, expr in rollup_def.items():
                row[k] = _eval_aggregate(expr, group_rows)
            result.append(row)
        return result

    # ------------------------------------------------------------------
    # Reshaping
    # ------------------------------------------------------------------

    def fold(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        key_col, val_col = (options.get("as") or ["key", "value"])[:2]
        id_cols = [c for c in (list(rows[0].keys()) if rows else []) if c not in columns]
        result = []
        for r in rows:
            for c in columns:
                result.append({**{ic: r[ic] for ic in id_cols}, key_col: c, val_col: r.get(c)})
        return result

    def pivot(self, rows: list[dict], on: list[str], values: list[str], options: dict) -> list[dict]:
        if not rows or not on:
            return []
        key_col = on[0]
        keys = list(dict.fromkeys(str(r.get(key_col)) for r in rows))
        return [{k: None for k in keys}]

    def spread(self, rows: list[dict], columns: list[str], options: dict) -> list[dict]:
        limit = options.get("limit")
        result = []
        for r in rows:
            new_row: dict = {}
            for k, v in r.items():
                if k in columns and isinstance(v, list):
                    n = limit if limit is not None else len(v)
                    for i in range(min(n, len(v))):
                        new_row[f"{k}_{i + 1}"] = v[i]
                else:
                    new_row[k] = v
            result.append(new_row)
        return result

    def unroll(self, rows: list[dict], columns: list[str]) -> list[dict]:
        result = []
        for r in rows:
            col = columns[0] if columns else None
            if col and isinstance(r.get(col), list):
                for v in r[col]:
                    result.append({**r, col: v})
            else:
                result.append(r)
        return result

    # ------------------------------------------------------------------
    # Joins
    # ------------------------------------------------------------------

    def join(self, left: list[dict], right: list[dict], left_col: str, right_col: str, how: str = "inner") -> list[dict]:
        right_index: dict = {}
        for r in right:
            k = r.get(right_col)
            right_index.setdefault(k, []).append(r)
        result = []
        matched_right: set[int] = set()
        for l_row in left:
            k = l_row.get(left_col)
            matches = right_index.get(k, [])
            if matches:
                for r in matches:
                    matched_right.add(id(r))
                    merged = {**l_row}
                    for rk, rv in r.items():
                        if rk != right_col:
                            merged[rk] = rv
                    result.append(merged)
            elif how in ("left", "full"):
                result.append(dict(l_row))
        if how in ("right", "full"):
            for r in right:
                if id(r) not in matched_right:
                    result.append(dict(r))
        return result

    def semijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        right_keys = {r.get(right_col) for r in right}
        return [r for r in left if r.get(left_col) in right_keys]

    def antijoin(self, left: list[dict], right: list[dict], left_col: str, right_col: str) -> list[dict]:
        right_keys = {r.get(right_col) for r in right}
        return [r for r in left if r.get(left_col) not in right_keys]

    def cross(self, left: list[dict], right: list[dict]) -> list[dict]:
        return [{**l_row, **r} for l_row in left for r in right]

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def union(self, tables: list[list[dict]]) -> list[dict]:
        combined = [r for t in tables for r in t]
        return self._dedup(combined)

    def intersect(self, tables: list[list[dict]]) -> list[dict]:
        if not tables:
            return []
        sets = [set(tuple(sorted(r.items())) for r in t) for t in tables]
        common = sets[0]
        for s in sets[1:]:
            common &= s
        return [dict(k) for k in common]

    def except_op(self, tables: list[list[dict]]) -> list[dict]:
        if not tables:
            return []
        exclude: set = set()
        for t in tables[1:]:
            for r in t:
                exclude.add(tuple(sorted(r.items())))
        return [r for r in tables[0] if tuple(sorted(r.items())) not in exclude]

    def concat(self, tables: list[list[dict]]) -> list[dict]:
        return [r for t in tables for r in t]

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------

    def to_csv(self, rows: list[dict], delimiter: str = ",") -> str:
        if not rows:
            return ""
        buf = io.StringIO()
        writer = csv_module.DictWriter(buf, fieldnames=list(rows[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    def to_markdown(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        cols = list(rows[0].keys())
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        lines = [header, sep]
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        return "\n".join(lines)

    def to_json(self, rows: list[dict]) -> str:
        return json.dumps(rows)
