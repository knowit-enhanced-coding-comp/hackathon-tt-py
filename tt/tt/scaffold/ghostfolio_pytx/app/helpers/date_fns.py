"""date_fns — Python equivalents of date-fns library functions."""
from __future__ import annotations

from datetime import datetime, timedelta, date as _date, timezone
from typing import Any

DATE_FORMAT = "yyyy-MM-dd"  # symbolic constant (not used directly)
_FMT = "%Y-%m-%d"


def _to_dt(d) -> datetime:
    """Coerce string / date / datetime to datetime."""
    if isinstance(d, datetime):
        return d
    if isinstance(d, _date):
        return datetime(d.year, d.month, d.day)
    if isinstance(d, str):
        return datetime.strptime(d, _FMT)
    raise TypeError(f"Cannot coerce {type(d)} to datetime")


def format(d, fmt: str = DATE_FORMAT) -> str:  # noqa: A001
    """Format a date — mirrors date-fns format()."""
    dt = _to_dt(d)
    # Map date-fns tokens to strftime
    py_fmt = (
        fmt.replace("yyyy", "%Y")
        .replace("MM", "%m")
        .replace("dd", "%d")
        .replace("MMMM", "%B")
        .replace("MMM", "%b")
        .replace("HH", "%H")
        .replace("mm", "%M")
        .replace("ss", "%S")
    )
    return dt.strftime(py_fmt)


# Alias used in translated code
format_date = format


def is_before(a, b) -> bool:
    return _to_dt(a) < _to_dt(b)


def is_after(a, b) -> bool:
    return _to_dt(a) > _to_dt(b)


def is_within_interval(date, interval: dict) -> bool:
    dt = _to_dt(date)
    return _to_dt(interval["start"]) <= dt <= _to_dt(interval["end"])


def is_same_day(a, b) -> bool:
    da = _to_dt(a)
    db = _to_dt(b)
    return da.year == db.year and da.month == db.month and da.day == db.day


def difference_in_days(a, b) -> int:
    return (_to_dt(a) - _to_dt(b)).days


def difference_in_years(a, b) -> int:
    da = _to_dt(a)
    db = _to_dt(b)
    return da.year - db.year - ((da.month, da.day) < (db.month, db.day))


def add_milliseconds(d, ms: int):
    return _to_dt(d) + timedelta(milliseconds=ms)


def add_days(d, days: int):
    return _to_dt(d) + timedelta(days=days)


def sub_days(d, days: int):
    return _to_dt(d) - timedelta(days=days)


def start_of_day(d):
    dt = _to_dt(d)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(d):
    dt = _to_dt(d)
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_year(d):
    dt = _to_dt(d)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_year(d):
    dt = _to_dt(d)
    return dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)


def start_of_month(d):
    dt = _to_dt(d)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(d):
    import calendar
    dt = _to_dt(d)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)


def each_day_of_interval(interval: dict):
    start = _to_dt(interval["start"])
    end = _to_dt(interval["end"])
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=1)
    return result


def each_year_of_interval(interval: dict):
    start = _to_dt(interval["start"])
    end = _to_dt(interval["end"])
    result = []
    year = start.year
    while True:
        dt = datetime(year, 1, 1)
        if dt > end:
            break
        result.append(dt)
        year += 1
    return result


def is_this_year(d) -> bool:
    return _to_dt(d).year == _date.today().year


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, _FMT)


def reset_hours(d) -> datetime:
    return _to_dt(d).replace(hour=0, minute=0, second=0, microsecond=0)


def min_date(*dates):
    return min(_to_dt(d) for d in dates)


def max_date(*dates):
    return max(_to_dt(d) for d in dates)


def get_interval_from_date_range(date_range: str) -> dict:
    """Return {startDate, endDate} for a given date range string."""
    today = _date.today()
    now = datetime(today.year, today.month, today.day)
    end = now

    if date_range == "max":
        start = datetime(2000, 1, 1)
    elif date_range == "1d":
        start = sub_days(now, 1)
    elif date_range == "1y":
        start = datetime(now.year - 1, now.month, now.day)
    elif date_range == "5y":
        start = datetime(now.year - 5, now.month, now.day)
    elif date_range == "ytd":
        start = datetime(now.year, 1, 1)
    elif date_range == "mtd":
        start = datetime(now.year, now.month, 1)
    elif date_range == "wtd":
        weekday = now.weekday()
        start = now - timedelta(days=weekday)
    elif len(date_range) == 4 and date_range.isdigit():
        # Year range like "2021"
        year = int(date_range)
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
    else:
        start = datetime(2000, 1, 1)

    return {"startDate": start, "endDate": end}
