"""Stub interfaces from @ghostfolio/common/interfaces"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssetProfileIdentifier:
    dataSource: str = ""
    symbol: str = ""


@dataclass
class SymbolMetrics:
    currentValues: dict = field(default_factory=dict)
    currentValuesWithCurrencyEffect: dict = field(default_factory=dict)
    grossPerformance: Any = None
    grossPerformanceWithCurrencyEffect: Any = None
    hasErrors: bool = False
    investment: Any = None
    investmentWithCurrencyEffect: Any = None
    netPerformance: Any = None
    netPerformanceWithCurrencyEffect: Any = None
    netPerformancePercentageWithCurrencyEffectMap: dict = field(default_factory=dict)
    netPerformanceValues: dict = field(default_factory=dict)
    netPerformanceValuesWithCurrencyEffect: dict = field(default_factory=dict)
    timeWeightedInvestment: Any = None
    timeWeightedInvestmentWithCurrencyEffect: Any = None
    totalDividend: Any = None
    totalDividendInBaseCurrency: Any = None
    totalInterest: Any = None
    totalInterestInBaseCurrency: Any = None
    totalInvestment: Any = None
    totalInvestmentWithCurrencyEffect: Any = None
