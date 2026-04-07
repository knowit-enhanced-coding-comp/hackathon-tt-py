"""Data models used by the portfolio calculator."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SymbolProfile:
    symbol: str
    data_source: str = "YAHOO"


@dataclass
class PortfolioOrderItem:
    date: str
    fee: Decimal
    quantity: Decimal
    symbol_profile: SymbolProfile
    type: str
    unit_price: Decimal
