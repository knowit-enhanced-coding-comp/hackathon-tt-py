"""Mirrors portfolio-order-item.interface.ts — extends PortfolioOrder for calculations."""
from __future__ import annotations

from dataclasses import dataclass, field

from .portfolio_order import PortfolioOrder


@dataclass
class PortfolioOrderItem(PortfolioOrder):
    item_type: str | None = None  # "start" | "end" | None
    unit_price_from_market_data: float | None = None
