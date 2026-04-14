"""Stub helpers from @ghostfolio/api/helper/portfolio.helper"""
from __future__ import annotations


def getFactor(order_type: str) -> int:
    """Return +1 for BUY, -1 for SELL."""
    return 1 if order_type == "BUY" else -1
