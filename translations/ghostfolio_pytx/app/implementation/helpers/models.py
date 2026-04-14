"""Stub models from @ghostfolio/common/models"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortfolioSnapshot:
    currentValueInBaseCurrency: Any = None
    grossPerformance: Any = None
    grossPerformanceWithCurrencyEffect: Any = None
    hasErrors: bool = False
    netPerformance: Any = None
    positions: list = field(default_factory=list)
    totalFeesWithCurrencyEffect: Any = None
    totalInterestWithCurrencyEffect: Any = None
    totalInvestment: Any = None
    totalInvestmentWithCurrencyEffect: Any = None


@dataclass
class TimelinePosition:
    dataSource: str = ""
    symbol: str = ""
    averagePrice: Any = None
    currency: str = ""
    feeInBaseCurrency: Any = None
    grossPerformance: Any = None
    grossPerformanceWithCurrencyEffect: Any = None
    includeInTotalAssetValue: bool = True
    investment: Any = None
    investmentWithCurrencyEffect: Any = None
    netPerformance: Any = None
    quantity: Any = None
    timeWeightedInvestment: Any = None
    timeWeightedInvestmentWithCurrencyEffect: Any = None
    valueInBaseCurrency: Any = None
