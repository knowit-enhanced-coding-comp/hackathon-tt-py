"""Decimal arithmetic helpers — Python equivalent of Big.js."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Iterable

getcontext().prec = 28


def to_decimal(value: int | float | str | Decimal | None, default: Decimal | None = None) -> Decimal:
    """Convert a value to Decimal. Returns default (or Decimal(0)) on None."""
    if value is None:
        return default if default is not None else Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def big_sum(values: Iterable[Decimal | int | float | None]) -> Decimal:
    """Sum an iterable of values using Decimal precision."""
    return sum((to_decimal(v) for v in values), Decimal(0))


def pct(numerator: Decimal | float | None, denominator: Decimal | float | None) -> Decimal:
    """Compute numerator / denominator as a percentage fraction.
    Returns 0 if denominator is zero or None.
    """
    n = to_decimal(numerator)
    d = to_decimal(denominator)
    if d == Decimal(0):
        return Decimal(0)
    return n / d
