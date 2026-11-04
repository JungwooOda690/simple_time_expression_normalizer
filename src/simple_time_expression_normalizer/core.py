"""Convert small natural-language time expressions to ``datetime`` objects.

The parser deliberately supports a narrow, well-defined grammar rather than
trying to understand arbitrary English.  That keeps the behaviour predictable
and makes every rule testable.  See the README for the exact grammar and the
one interpretation chosen where the brief was ambiguous.
"""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from typing import Callable, Optional

__all__ = ["normalize", "normalize_or_none"]


# A clock is any callable returning a timezone-naive ``datetime``.  Taking it as
# a parameter (rather than calling ``datetime.now`` internally) is what lets the
# tests be deterministic: they pass a fixed clock instead of sleeping or
# asserting on wall-clock time.
Clock = Callable[[], datetime]


_DAY_OFFSETS = {
    "today": 0,
    "tomorrow": 1,
    "yesterday": -1,
}

# ``now`` is the only bare word that resolves to an instant rather than a date.
_TIME_RE = re.compile(
    r"^(?P<hour>\d{1,2})"
    r"(?::(?P<minute>\d{2}))?"
    r"(?:\s*(?P<meridiem>am|pm))?$",
    re.IGNORECASE,
)


def _default_clock() -> datetime:
    """Return the current local time.

    Kept as a small named function so tests can substitute a fake clock without
    reaching into module internals.
    """
    return datetime.now()


def _parse_time_of_day(token: str) -> time:
    """Parse ``5``, ``5pm``, ``17:30`` or ``5:30 am`` into a ``time``.

    Raises ``ValueError`` for anything that is not a valid time of day.  The
    caller decides whether that is an error or a reason to return ``None``.
    """
    match = _TIME_RE.match(token)
    if match is None:
        raise ValueError(f"unrecognised time of day: {token!r}")

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    meridiem = match.group("meridiem")

    if meridiem is not None:
        # 12am is midnight and 12pm is noon; every other pm hour shifts by 12.
        if not 1 <= hour <= 12:
            raise ValueError(f"hour out of range for 12-hour clock: {hour}")
        if meridiem.lower() == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
    else:
        if not 0 <= hour <= 23:
            raise ValueError(f"hour out of range: {hour}")

    if not 0 <= minute <= 59:
        raise ValueError(f"minute out of range: {minute}")

    return time(hour=hour, minute=minute)


def _parse_day_offset(token: str) -> int:
    """Map a day word to a signed offset from the clock's date."""
    try:
        return _DAY_OFFSETS[token]
    except KeyError:
        raise ValueError(f"unrecognised day: {token!r}") from None


def normalize(expression: str, *, now: Optional[Clock] = None) -> datetime:
    """Return the ``datetime`` described by *expression*.

    Supported forms (case-insensitive, surrounding whitespace ignored):

    * ``now``
    * ``today``, ``tomorrow``, ``yesterday`` (midnight on that day)
    * ``today at 5``, ``tomorrow at 17:30``, ``yesterday at 5:30 am``
    * ``5pm``, ``5:30 am``, ``17:30`` (today at that time)

    ``now`` must be a callable returning a timezone-naive ``datetime``.  It
    defaults to ``datetime.now``.  Passing a fake clock is the supported way to
    make results deterministic in tests.

    Raises ``ValueError`` if the expression is empty or does not match the
    grammar above.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")

    clock = _default_clock if now is None else now
    text = expression.strip().lower()
    if not text:
        raise ValueError("empty time expression")

    base = clock()

    if text == "now":
        return base

    if text in _DAY_OFFSETS:
        day = base.date() + timedelta(days=_DAY_OFFSETS[text])
        return datetime.combine(day, time.min)

    # ``<day> at <time>``
    if " at " in text:
        day_part, _, time_part = text.partition(" at ")
        offset = _parse_day_offset(day_part.strip())
        at = _parse_time_of_day(time_part.strip())
        day = base.date() + timedelta(days=offset)
        return datetime.combine(day, at)

    # Bare time of day: anchor to today.
    at = _parse_time_of_day(text)
    return datetime.combine(base.date(), at)


def normalize_or_none(expression: str, *, now: Optional[Clock] = None) -> Optional[datetime]:
    """Like :func:`normalize` but return ``None`` instead of raising.

    Useful when scanning free text for time references and a miss is not an
    error.  The clock is still honoured so callers get the same determinism as
    with :func:`normalize`.
    """
    try:
        return normalize(expression, now=now)
    except (ValueError, TypeError):
        return None
