"""Stub ROAI calculator — returns zero/empty values for all metrics.

This is the example skeleton: it has the correct interface but no real
calculation logic. Tests will fail on value assertions but all endpoints
will run without errors.
"""
from __future__ import annotations

from ..portfolio_calculator import PortfolioCalculator
from ...interfaces import SymbolMetrics


class RoaiPortfolioCalculator(PortfolioCalculator):
    """Stub ROAI calculator — no real implementation."""

    def compute(self) -> dict:
        sorted_acts = self.sorted_activities()

        # Extract unique symbols from activities (no computation)
        symbols: dict[str, dict] = {}
        for act in sorted_acts:
            sym = act.get("symbol", "")
            if act.get("type", "") in ("DIVIDEND", "FEE", "LIABILITY"):
                continue
            if sym and sym not in symbols:
                symbols[sym] = {
                    "quantity": 0.0,
                    "investment": 0.0,
                    "avg_price": 0.0,
                    "total_buy_cost": 0.0,
                    "realized_pnl": 0.0,
                }

        return {
            "symbols": symbols,
            "investment_deltas": [],
            "total_fees": 0.0,
            "sorted_activities": sorted_acts,
        }

    def get_symbol_metrics(self, symbol: str) -> SymbolMetrics:
        return SymbolMetrics()
