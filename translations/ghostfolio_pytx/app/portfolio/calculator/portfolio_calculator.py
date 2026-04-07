"""Mirrors calculator/portfolio-calculator.ts — abstract base class.

In the original Ghostfolio this base class handles transaction point
computation, caching, exchange rates, and data gathering. Subclasses
(ROAI, ROI, MWR, TWR) implement the actual performance formulas.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..current_rate_service import CurrentRateService
from ..interfaces import SymbolMetrics


_TYPE_ORDER = {"BUY": 0, "SELL": 1, "DIVIDEND": 2, "FEE": 3, "LIABILITY": 4}


class PortfolioCalculator(ABC):
    """Base class for portfolio calculators."""

    def __init__(
        self,
        activities: list[dict],
        current_rate_service: CurrentRateService,
    ) -> None:
        self.activities = activities
        self.current_rate_service = current_rate_service

    def sorted_activities(self) -> list[dict]:
        return sorted(
            self.activities,
            key=lambda a: (a["date"], _TYPE_ORDER.get(a.get("type", ""), 5)),
        )

    @abstractmethod
    def compute(self) -> dict:
        """Return full portfolio computation result.

        Returns dict with keys: symbols, investment_deltas, total_fees,
        sorted_activities.
        """

    @abstractmethod
    def get_symbol_metrics(self, symbol: str) -> SymbolMetrics:
        """Return per-symbol position metrics."""
