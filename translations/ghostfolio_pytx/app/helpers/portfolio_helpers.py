"""Portfolio helpers — Python equivalents of Ghostfolio portfolio helper functions."""
from __future__ import annotations

from app.helpers.big import Big


def get_factor(activity_type: str) -> int:
    """Return 1 for BUY/DIVIDEND/INTEREST, -1 for SELL/FEE/LIABILITY."""
    if activity_type in ("BUY", "DIVIDEND", "INTEREST", "ITEM", "VALUABLE"):
        return 1
    elif activity_type in ("SELL", "FEE", "LIABILITY"):
        return -1
    return 1


INVESTMENT_ACTIVITY_TYPES = {"BUY", "SELL"}
