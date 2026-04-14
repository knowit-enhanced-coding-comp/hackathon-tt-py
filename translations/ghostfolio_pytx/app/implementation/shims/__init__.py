"""Shims package — Python equivalents for JavaScript/TypeScript runtime primitives."""
from .nulls import nullish, safe_get
from .numbers import to_decimal, big_sum, pct
from .dates import (
    parse_date,
    format_date,
    difference_in_days,
    each_day_of_interval,
    each_year_of_interval,
    start_of_year,
    end_of_year,
    add_days,
    is_before,
    is_after,
    is_this_year,
    reset_hours,
)
from .collections import deep_copy, sort_by, group_by, uniq_by, sum_by
from .decorators import injectable, controller, log_performance

__all__ = [
    "nullish",
    "safe_get",
    "to_decimal",
    "big_sum",
    "pct",
    "parse_date",
    "format_date",
    "difference_in_days",
    "each_day_of_interval",
    "each_year_of_interval",
    "start_of_year",
    "end_of_year",
    "add_days",
    "is_before",
    "is_after",
    "is_this_year",
    "reset_hours",
    "deep_copy",
    "sort_by",
    "group_by",
    "uniq_by",
    "sum_by",
    "injectable",
    "controller",
    "log_performance",
]
