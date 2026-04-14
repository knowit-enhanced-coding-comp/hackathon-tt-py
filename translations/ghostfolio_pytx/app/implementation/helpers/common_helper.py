"""Stub helpers from @ghostfolio/common/helper"""
from __future__ import annotations
from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"


def parseDate(s: str) -> date:
    return datetime.strptime(s[:10], DATE_FORMAT).date()


def resetHours(d: date) -> date:
    return d


def getSum(items, key):
    return sum(item.get(key, 0) for item in items) if items else 0
