"""Date utilities — Python equivalents of date-fns functions."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Iterator

DATE_FORMAT = "%Y-%m-%d"


def parse_date(s: str | None) -> date | None:
    """Parse ISO date string YYYY-MM-DD → date. Returns None on failure."""
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], DATE_FORMAT).date()
    except ValueError:
        return None


def format_date(d: date | datetime | None) -> str | None:
    """Format date to YYYY-MM-DD string."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.strftime(DATE_FORMAT)
    return d.strftime(DATE_FORMAT)


def difference_in_days(date_left: date, date_right: date) -> int:
    """Return (date_left - date_right) in days. Equivalent to date-fns differenceInDays."""
    return (date_left - date_right).days


def each_day_of_interval(start: date, end: date) -> Iterator[date]:
    """Yield each date in [start, end] inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def each_year_of_interval(start: date, end: date) -> list[date]:
    """Return the first day of each year in [start, end]. Equivalent to date-fns eachYearOfInterval."""
    years = []
    year = start.year
    while year <= end.year:
        years.append(date(year, 1, 1))
        year += 1
    return years


def start_of_year(d: date) -> date:
    return date(d.year, 1, 1)


def end_of_year(d: date) -> date:
    return date(d.year, 12, 31)


def add_days(d: date, n: int) -> date:
    return d + timedelta(days=n)


def is_before(d1: date, d2: date) -> bool:
    return d1 < d2


def is_after(d1: date, d2: date) -> bool:
    return d1 > d2


def is_this_year(d: date) -> bool:
    return d.year == datetime.now().year


def reset_hours(d: date) -> date:
    """Return date with time reset to midnight (date-only)."""
    return d if isinstance(d, date) and not isinstance(d, datetime) else d.date()


def add_milliseconds(d: date | datetime, ms: int) -> datetime:
    """Add milliseconds to a date/datetime."""
    if isinstance(d, date) and not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    return d + timedelta(milliseconds=ms)


def format(d: date | datetime | None, fmt: str = DATE_FORMAT) -> str | None:
    """Format date. date-fns format equivalent."""
    return format_date(d)


# camelCase aliases used by translated code
parseDate = parse_date
formatDate = format_date
differenceInDays = difference_in_days
eachDayOfInterval = each_day_of_interval
eachYearOfInterval = each_year_of_interval
startOfYear = start_of_year
endOfYear = end_of_year
addDays = add_days
addMilliseconds = add_milliseconds
isBefore = is_before
isAfter = is_after
isThisYear = is_this_year
resetHours = reset_hours
