# simple_time_expression_normalizer

Converts small natural-language time references such as `now`, `today at 5` or
`tomorrow at 17:30` into `datetime` objects.

```python
from datetime import datetime
from simple_time_expression_normalizer import normalize, normalize_or_none

# Pass a clock so the result is deterministic.  Without one, the library uses
# datetime.now().
clock = lambda: datetime(2024, 3, 15, 9, 30, 0)

print(normalize("now", now=clock))              # 2024-03-15 09:30:00
print(normalize("today at 5", now=clock))       # 2024-03-15 05:00:00
print(normalize("tomorrow at 17:30", now=clock))  # 2024-03-16 17:30:00
print(normalize("5pm", now=clock))              # 2024-03-15 17:00:00
print(normalize_or_none("soon", now=clock))     # None
```

## Why this exists

Most natural-language date libraries try to cover a huge grammar and quietly
return surprising results when they guess wrong.  This one supports a small,
explicit set of forms and raises `ValueError` for anything else, so the caller
always knows whether a string was understood.

The trade-off is coverage: it will not parse `next Tuesday`, `in two hours` or
`the day after tomorrow`.  Those are deliberately out of scope.  The benefit is
that every accepted input has exactly one documented meaning.

## Supported expressions

Case and surrounding whitespace are ignored.

- `now`
- `today`, `tomorrow`, `yesterday` — midnight on that day
- `<day> at <time>` — for example `today at 5`, `tomorrow at 17:30`, `yesterday at 5:30 am`
- a bare time of day — `5pm`, `5:30 am`, `17:30` — anchored to today

Times may be written as `5`, `5pm`, `5:30 am` or `17:30`.  The 12-hour forms
accept hours 1–12; the 24-hour forms accept hours 0–23.  Minutes must be 0–59.

## The awkward edge

A bare time of day such as `5pm` is always anchored to *today*, even when that
instant is already in the past relative to the supplied clock.  For example,
with a clock of 18:00, `normalize("5pm")` still returns 17:00 today.  The
library does not roll forward to tomorrow; that decision belongs to the caller,
who may have a different notion of “today” (timezone, business day, etc.).

## API

- `normalize(expression, *, now=None)` — returns a `datetime` or raises
  `ValueError` (and `TypeError` for non-string input).
- `normalize_or_none(expression, *, now=None)` — returns a `datetime` or `None`.

The `now` argument is any callable returning a timezone-naive `datetime`.  It
defaults to `datetime.now`.  Supplying a fixed clock is the supported way to
make results deterministic in tests.
