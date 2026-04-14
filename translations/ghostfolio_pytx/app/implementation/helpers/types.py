"""Stub types from @ghostfolio/common/types"""
from __future__ import annotations
from typing import Literal

DateRange = Literal["1d", "1y", "5y", "max", "mtd", "wtd", "ytd"]

PerformanceCalculationType = Literal["ROAI", "TWR", "MWR"]

GroupBy = Literal["day", "month", "year"]
